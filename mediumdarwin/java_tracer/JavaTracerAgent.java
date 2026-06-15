
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.lang.instrument.IllegalClassFormatException;
import java.security.ProtectionDomain;
import java.net.URL;
import java.net.URLDecoder;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.jar.JarFile;

import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.Type;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.AnnotationNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.FrameNode;
import org.objectweb.asm.tree.InsnList;
import org.objectweb.asm.tree.InsnNode;
import org.objectweb.asm.tree.JumpInsnNode;
import org.objectweb.asm.tree.LabelNode;
import org.objectweb.asm.tree.LineNumberNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;
import org.objectweb.asm.tree.TryCatchBlockNode;
import org.objectweb.asm.tree.VarInsnNode;

/**
 * MediumDarwin coverage-only Java agent.
 *
 * Purpose: - Collect statement/line coverage precisely and map executed
 * statements to tests.
 *
 * Non-goals: - No variable tracing / trace.json output.
 *
 * Output: - Per-process JSON files (coverageFile.<pid>.json) that will be
 * merged by Python code after all JVMs exit. The merged file is compatible with
 * MediumDarwin's LineCoverage._import_java_tracer_coverage_to_db().
 *
 * Args format (compatible with previous agent): -
 * outputFile@@projectRoot@@coverageFile
 *
 * We ignore outputFile (trace file) in this coverage-only agent. Merging of
 * per-process files is handled by Python code, not in this agent.
 */
public class JavaTracerAgent {

    private static Instrumentation inst;
    private static String projectRoot;
    // Base coverage file name (used to derive per-process filename)
    private static String coverageFile;
    // Per-process coverage file (this JVM writes only this file)
    private static String coverageFilePid;

    // Thread-local test context: internalClassName:methodName
    private static final ThreadLocal<String> currentTest = new ThreadLocal<>();

    // statementKey -> tests (internalClass:method keys)
    private static final Map<String, Set<String>> statementToTests
            = Collections.synchronizedMap(new LinkedHashMap<>());

    public static void premain(String agentArgs, Instrumentation inst) {
        JavaTracerAgent.inst = inst;
        parseArgs(agentArgs);

        // Append agent jar to system classloader search (helps with classloader edge cases).
        try {
            URL loc = JavaTracerAgent.class.getProtectionDomain() != null
                    && JavaTracerAgent.class.getProtectionDomain().getCodeSource() != null
                    ? JavaTracerAgent.class.getProtectionDomain().getCodeSource().getLocation()
                    : null;
            if (loc != null) {
                String p = URLDecoder.decode(loc.getPath(), StandardCharsets.UTF_8.name());
                if (p != null && p.endsWith(".jar")) {
                    inst.appendToSystemClassLoaderSearch(new JarFile(p));
                }
            }
        } catch (Throwable ignored) {
        }

        try {
            inst.addTransformer(new CoverageTransformer(), true);
        } catch (Throwable t) {
            // Fallback: without retransformation
            try {
                inst.addTransformer(new CoverageTransformer(), false);
            } catch (Throwable ignored) {
            }
        }

        Runtime.getRuntime().addShutdownHook(new Thread(JavaTracerAgent::shutdown));
    }

    private static void parseArgs(String agentArgs) {
        // Default values (safe)
        projectRoot = ".";
        coverageFile = "trace_coverage.json";

        if (agentArgs == null || agentArgs.isEmpty()) {
            return;
        }

        // Backwards compatible format: outputFile@@projectRoot@@coverageFile
        String[] args = agentArgs.split("@@");
        if (args.length >= 2) {
            projectRoot = args[1];
        }
        if (args.length >= 3) {
            coverageFile = args[2];
        }

        // IMPORTANT (Gradle parallel forks):
        // Gradle often runs tests in multiple JVMs. If every JVM writes the same coverageFile path,
        // the last process to exit wins and we lose coverage from other forks (e.g., Spock).
        // Write per-process coverage files; Python code will merge them after all JVMs exit.
        coverageFilePid = withPidSuffix(coverageFile);
    }

    private static String withPidSuffix(String path) {
        if (path == null || path.isEmpty()) {
            return path;
        }
        String pid = "pid";
        try {
            // Format: "<pid>@<hostname>"
            String name = ManagementFactory.getRuntimeMXBean().getName();
            int at = name.indexOf('@');
            pid = (at > 0) ? name.substring(0, at) : name;
            if (pid == null || pid.isEmpty()) {
                pid = "pid";
            }
        } catch (Throwable ignored) {
        }

        // Avoid double suffixing
        if (path.contains("." + pid + ".json")) {
            return path;
        }
        if (path.endsWith(".json")) {
            return path.substring(0, path.length() - 5) + "." + pid + ".json";
        }
        return path + "." + pid;
    }

    /**
     * Set the current test context.
     */
    public static void setCurrentTest(String testMethodKey) {
        currentTest.set(testMethodKey);
    }

    /**
     * Clear the current test context.
     */
    public static void clearCurrentTest() {
        currentTest.remove();
    }

    /**
     * Record coverage for a statement execution.
     */
    public static void recordCoverage(String filename, int lineNumber, String className, String methodName) {
        // Use a stable statement key format.
        String key = filename + ":" + lineNumber + ":" + className + ":" + methodName;

        String test = currentTest.get();
        if (test == null) {
            test = "unknown";
        }

        Set<String> testsForStmt = statementToTests
                .computeIfAbsent(key, k -> Collections.synchronizedSet(new LinkedHashSet<>()));
        testsForStmt.add(test);

        // Spock/Groovy features can have quoted names (spaces) and some runners report them inconsistently.
        // To keep selection robust, also record a class-level test key when the method name looks "feature-like".
        // This makes downstream selection able to run the whole spec class even if method-level matching differs.
        int idx = test.indexOf(':');
        if (idx > 0) {
            String cls = test.substring(0, idx);
            String meth = test.substring(idx + 1);
            if (meth.indexOf(' ') >= 0) {
                testsForStmt.add(cls);
            }
        }
    }

    static class CoverageTransformer implements ClassFileTransformer {

        // Spock feature mapping: spec internal class name -> featurePrefix -> feature display name
        // featurePrefix looks like "$spock_feature_0_0"
        private static final Map<String, Map<String, String>> spockFeatureNameCache = new ConcurrentHashMap<>();

        @Override
        public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                ProtectionDomain protectionDomain, byte[] classfileBuffer)
                throws IllegalClassFormatException {
            if (className == null || classfileBuffer == null) {
                return null;
            }

            // Always skip agent itself
            if ("JavaTracerAgent".equals(className) || className.startsWith("JavaTracerAgent$")) {
                return null;
            }

            // Skip Gradle / runtime infrastructure to avoid breaking test executors
            if (className.startsWith("worker/")
                    || className.startsWith("org/gradle/")
                    || className.startsWith("org/slf4j/")
                    || className.startsWith("ch/qos/logback/")
                    || className.startsWith("org/apache/logging/")
                    || className.startsWith("kotlin/")
                    || className.startsWith("org/jetbrains/")) {
                return null;
            }

            // Skip JDK / common libraries / test frameworks (never instrument these)
            if (className.startsWith("java/")
                    || className.startsWith("javax/")
                    || className.startsWith("sun/")
                    || className.startsWith("com/sun/")
                    || className.startsWith("jdk/")
                    || className.startsWith("org/objectweb/asm/")
                    || className.startsWith("org/junit/")
                    || className.startsWith("junit/")
                    || className.startsWith("org/testng/")
                    || className.startsWith("org/hamcrest/")
                    || className.startsWith("org/mockito/")
                    || className.startsWith("spock/")
                    || className.startsWith("groovy/")) {
                return null;
            }

            // Only instrument classes that are under projectRoot (strict safety).
            if (isDefinitelyNotFromProject(protectionDomain)) {
                return null;
            }

            try {
                ClassReader cr = new ClassReader(classfileBuffer);
                ClassNode cn = new ClassNode();
                cr.accept(cn, ClassReader.EXPAND_FRAMES);

                // Cache Spock feature names for this spec class (if applicable).
                boolean isSpockSpec = (cn.superName != null && "spock/lang/Specification".equals(cn.superName));
                if (isSpockSpec && cn.name != null && cn.methods != null) {
                    Map<String, String> featureMap = spockFeatureNameCache.computeIfAbsent(
                            cn.name, k -> new ConcurrentHashMap<>());
                    for (MethodNode mn : cn.methods) {
                        if (mn == null || mn.name == null) {
                            continue;
                        }
                        if (!mn.name.startsWith("$spock_feature_")) {
                            continue;
                        }
                        String feature = spockFeatureName(mn);
                        if (feature == null || feature.isEmpty()) {
                            continue;
                        }
                        String prefix = spockFeaturePrefix(mn.name);
                        if (prefix != null && !prefix.isEmpty()) {
                            featureMap.put(prefix, feature);
                        }
                    }
                }

                boolean modified = false;
                for (MethodNode mn : cn.methods) {
                    if (mn == null) {
                        continue;
                    }
                    if ((mn.access & (Opcodes.ACC_ABSTRACT | Opcodes.ACC_NATIVE)) != 0) {
                        continue;
                    }
                    if ("<clinit>".equals(mn.name)) {
                        continue;
                    }

                    boolean isTest = isTestMethod(cn, mn);
                    if (isTest) {
                        modified |= instrumentTestContext(cn, mn);
                    }
                    modified |= instrumentCoverage(cn, mn, protectionDomain);
                }

                if (!modified) {
                    return null;
                }

                ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES);
                cn.accept(cw);
                return cw.toByteArray();
            } catch (Throwable t) {
                // Fail-safe: don't break the JVM; just skip this class
                return null;
            }
        }

        private String spockFeaturePrefix(String methodName) {
            // Extract "$spock_feature_X_Y" from "$spock_feature_X_Y" or "$spock_feature_X_Y_closure1" etc.
            if (methodName == null) {
                return null;
            }
            if (!methodName.startsWith("$spock_feature_")) {
                return null;
            }
            String[] parts = methodName.split("_");
            // Expect: ["$spock", "feature", X, Y, ...]
            if (parts.length < 4) {
                return methodName;
            }
            return parts[0] + "_" + parts[1] + "_" + parts[2] + "_" + parts[3];
        }

        private boolean isDefinitelyNotFromProject(ProtectionDomain protectionDomain) {
            if (projectRoot == null || projectRoot.isEmpty()) {
                return false;
            }
            // If we can't determine the code source, don't skip (we already have strong package-based skips above).
            if (protectionDomain == null || protectionDomain.getCodeSource() == null
                    || protectionDomain.getCodeSource().getLocation() == null) {
                return false;
            }
            try {
                String locationPath = protectionDomain.getCodeSource().getLocation().getPath();
                if (locationPath == null) {
                    return false;
                }
                String decodedPath = URLDecoder.decode(locationPath, StandardCharsets.UTF_8.name());
                if (decodedPath.matches("^/[A-Za-z]:/.*")) {
                    decodedPath = decodedPath.substring(1);
                }
                Path rootPath = Paths.get(projectRoot).toAbsolutePath().normalize();
                Path classPath = Paths.get(decodedPath).toAbsolutePath().normalize();
                if (classPath.toFile().isFile()) {
                    classPath = classPath.getParent();
                }
                return !classPath.startsWith(rootPath);
            } catch (Exception e) {
                return false;
            }
        }

        private boolean isTestMethod(ClassNode cn, MethodNode mn) {
            // JUnit3 style
            if (mn.name != null && mn.name.startsWith("test") && mn.name.length() > 4) {
                char c = mn.name.charAt(4);
                if (Character.isUpperCase(c) || Character.isDigit(c)) {
                    return true;
                }
            }

            // Annotation-based: JUnit4/5/TestNG often contain "Test"
            if (mn.visibleAnnotations != null) {
                for (AnnotationNode ann : mn.visibleAnnotations) {
                    if (ann != null && ann.desc != null && ann.desc.contains("Test")) {
                        return true;
                    }
                }
            }

            // Spock (Groovy): classes extend spock/lang/Specification.
            // IMPORTANT: Spock feature methods are compiled to "$spock_feature_*" methods.
            boolean isSpock = (cn.superName != null && "spock/lang/Specification".equals(cn.superName));
            if (isSpock) {
                if (mn.name == null || mn.name.startsWith("<")) {
                    return false;
                }
                // Skip lifecycle / helper methods
                if (mn.name.equals("setup") || mn.name.equals("cleanup")
                        || mn.name.equals("setupSpec") || mn.name.equals("cleanupSpec")
                        || mn.name.startsWith("$spock_initializeFields")
                        || mn.name.startsWith("$spock_closure")
                        || mn.name.startsWith("$get")
                        || mn.name.startsWith("$set")) {
                    return false;
                }
                // Spock features are "$spock_feature_*" (usually public instance).
                if (mn.name.startsWith("$spock_feature_")) {
                    return true;
                }
                // Fall back: public instance methods are potential features
                return ((mn.access & Opcodes.ACC_PUBLIC) != 0
                        && (mn.access & Opcodes.ACC_STATIC) == 0);
            }

            // Heuristic: in classes whose name contains "Test", treat public instance methods starting with lowercase as tests
            if (cn.name != null && (cn.name.contains("Test") || cn.name.endsWith("Test"))) {
                if (mn.name != null && !mn.name.startsWith("<") && mn.name.length() > 0) {
                    char first = mn.name.charAt(0);
                    if (Character.isLowerCase(first)
                            && (mn.access & Opcodes.ACC_PUBLIC) != 0
                            && (mn.access & Opcodes.ACC_STATIC) == 0) {
                        return true;
                    }
                }
            }

            return false;
        }

        private String spockFeatureName(MethodNode mn) {
            // Try to extract the human-readable feature name from Spock's FeatureMetadata annotation.
            // Descriptor varies by Spock version; we do a contains() match to keep it flexible.
            if (mn == null || mn.visibleAnnotations == null) {
                return null;
            }
            for (AnnotationNode ann : mn.visibleAnnotations) {
                if (ann == null || ann.desc == null) {
                    continue;
                }
                // e.g. "Lorg/spockframework/runtime/model/FeatureMetadata;"
                if (!ann.desc.contains("FeatureMetadata")) {
                    continue;
                }
                if (ann.values == null) {
                    continue;
                }
                // ann.values is [key1, val1, key2, val2, ...]
                for (int i = 0; i + 1 < ann.values.size(); i += 2) {
                    Object k = ann.values.get(i);
                    Object v = ann.values.get(i + 1);
                    if ("name".equals(k) && v instanceof String) {
                        String s = (String) v;
                        if (!s.isEmpty()) {
                            return s;
                        }
                    }
                }
            }
            return null;
        }

        private String testKeyForMethod(ClassNode cn, MethodNode mn) {
            if (cn == null || mn == null) {
                return "unknown";
            }
            boolean isSpock = (cn.superName != null && "spock/lang/Specification".equals(cn.superName));
            if (isSpock && mn.name != null && mn.name.startsWith("$spock_feature_")) {
                String feature = spockFeatureName(mn);
                if (feature == null || feature.isEmpty()) {
                    // For helper/closure methods, FeatureMetadata may not be present; use cached mapping from prefix.
                    String prefix = spockFeaturePrefix(mn.name);
                    Map<String, String> featureMap = (cn.name != null) ? spockFeatureNameCache.get(cn.name) : null;
                    if (featureMap != null && prefix != null) {
                        feature = featureMap.get(prefix);
                    }
                }
                if (feature != null) {
                    return cn.name + ":" + feature;
                }
            }
            return cn.name + ":" + (mn.name != null ? mn.name : "unknown");
        }

        private InsnList buildSetTestContext(String testKey) {
            InsnList il = new InsnList();
            il.add(new org.objectweb.asm.tree.LdcInsnNode(testKey));
            il.add(new MethodInsnNode(
                    Opcodes.INVOKESTATIC,
                    "JavaTracerAgent",
                    "setCurrentTest",
                    "(Ljava/lang/String;)V",
                    false));
            return il;
        }

        private InsnList buildClearTestContext() {
            InsnList il = new InsnList();
            il.add(new MethodInsnNode(
                    Opcodes.INVOKESTATIC,
                    "JavaTracerAgent",
                    "clearCurrentTest",
                    "()V",
                    false));
            return il;
        }

        private boolean instrumentTestContext(ClassNode cn, MethodNode mn) {
            AbstractInsnNode first = mn.instructions != null ? mn.instructions.getFirst() : null;
            if (first == null) {
                return false;
            }

            // Insert setCurrentTest at method entry
            mn.instructions.insertBefore(first, buildSetTestContext(testKeyForMethod(cn, mn)));

            // Insert clearCurrentTest before all return instructions
            List<AbstractInsnNode> returns = new ArrayList<>();
            AbstractInsnNode cur = first;
            while (cur != null) {
                int op = cur.getOpcode();
                if (op == Opcodes.RETURN
                        || op == Opcodes.ARETURN
                        || op == Opcodes.IRETURN
                        || op == Opcodes.LRETURN
                        || op == Opcodes.FRETURN
                        || op == Opcodes.DRETURN) {
                    returns.add(cur);
                }
                cur = cur.getNext();
            }
            for (int i = returns.size() - 1; i >= 0; i--) {
                mn.instructions.insertBefore(returns.get(i), buildClearTestContext());
            }

            // Also clear on exception: add catch-all handler that clears and rethrows
            LabelNode tryStart = new LabelNode();
            LabelNode tryEnd = new LabelNode();
            LabelNode catchStart = new LabelNode();
            // Place tryStart right after the setCurrentTest call we inserted (at very beginning)
            AbstractInsnNode bodyStart = mn.instructions.getFirst();
            mn.instructions.insert(bodyStart, tryStart);
            // Put tryEnd at the end of method (before any existing tail)
            mn.instructions.add(tryEnd);

            int exVar = mn.maxLocals;
            mn.maxLocals = exVar + 1;
            InsnList catchBlock = new InsnList();
            catchBlock.add(catchStart);
            catchBlock.add(new VarInsnNode(Opcodes.ASTORE, exVar));
            catchBlock.add(buildClearTestContext());
            catchBlock.add(new VarInsnNode(Opcodes.ALOAD, exVar));
            catchBlock.add(new InsnNode(Opcodes.ATHROW));
            mn.instructions.add(catchBlock);

            mn.tryCatchBlocks.add(new TryCatchBlockNode(
                    tryStart, tryEnd, catchStart, "java/lang/Throwable"));

            return true;
        }

        private boolean instrumentCoverage(ClassNode cn, MethodNode mn, ProtectionDomain protectionDomain) {
            if (mn.instructions == null || mn.instructions.getFirst() == null) {
                return false;
            }

            boolean modified = false;
            // Get full file path relative to projectRoot
            String sourceFile = getFullFilePath(cn, protectionDomain);
            Set<Integer> seenLines = new LinkedHashSet<>();

            AbstractInsnNode cur = mn.instructions.getFirst();
            int currentLine = -1;
            boolean inConstructor = "<init>".equals(mn.name);
            boolean constructorInitialized = !inConstructor;

            while (cur != null) {
                AbstractInsnNode next = cur.getNext();

                // Mark constructor initialized after super/this ctor call
                if (!constructorInitialized && cur instanceof MethodInsnNode) {
                    MethodInsnNode mi = (MethodInsnNode) cur;
                    if (mi.getOpcode() == Opcodes.INVOKESPECIAL && "<init>".equals(mi.name)) {
                        constructorInitialized = true;
                    }
                }

                if (cur instanceof LineNumberNode) {
                    LineNumberNode ln = (LineNumberNode) cur;
                    currentLine = ln.line;
                } else if (constructorInitialized && currentLine > 0) {
                    // Only inject once per (method,line) and avoid noisy nodes
                    if (!seenLines.contains(currentLine)
                            && !(cur instanceof LabelNode)
                            && !(cur instanceof FrameNode)
                            && !(cur instanceof LineNumberNode)
                            && !(cur instanceof JumpInsnNode)) {
                        seenLines.add(currentLine);
                        InsnList il = new InsnList();
                        il.add(new org.objectweb.asm.tree.LdcInsnNode(sourceFile));
                        addInt(il, currentLine);
                        il.add(new org.objectweb.asm.tree.LdcInsnNode(cn.name));
                        il.add(new org.objectweb.asm.tree.LdcInsnNode(mn.name));
                        il.add(new MethodInsnNode(
                                Opcodes.INVOKESTATIC,
                                "JavaTracerAgent",
                                "recordCoverage",
                                "(Ljava/lang/String;ILjava/lang/String;Ljava/lang/String;)V",
                                false));
                        mn.instructions.insertBefore(cur, il);
                        modified = true;
                    }
                }

                cur = next;
            }

            return modified;
        }

        private String simpleName(String internalName) {
            int idx = internalName != null ? internalName.lastIndexOf('/') : -1;
            if (idx >= 0 && idx < internalName.length() - 1) {
                return internalName.substring(idx + 1);
            }
            return internalName != null ? internalName : "Unknown";
        }

        /**
         * Try to find the actual source file by searching common source
         * directories. Returns the actual Path if found, or null if not found.
         */
        private Path findActualSourceFile(Path projectRoot, String className, String sourceFileName) {
            if (projectRoot == null || className == null || sourceFileName == null) {
                return null;
            }

            try {
                // Extract package path from class internal name
                String packagePath = "";
                int lastSlash = className.lastIndexOf('/');
                if (lastSlash >= 0) {
                    packagePath = className.substring(0, lastSlash);
                }
                String packagePathFs = packagePath.replace('/', File.separatorChar);

                // Common source directory candidates to search
                String[] sourceDirs = {
                    "src/test/java",
                    "src/test/groovy",
                    "src/main/java",
                    "src/main/groovy",
                    "src/java",
                    "src/groovy"
                };

                // Search in each source directory
                for (String sourceDir : sourceDirs) {
                    Path candidate = projectRoot.resolve(sourceDir);
                    if (packagePathFs.isEmpty()) {
                        candidate = candidate.resolve(sourceFileName);
                    } else {
                        candidate = candidate.resolve(packagePathFs).resolve(sourceFileName);
                    }
                    if (Files.exists(candidate)) {
                        return candidate;
                    }
                }
            } catch (Exception e) {
                // If anything fails, return null to fall back to inference
            }
            return null;
        }

        /**
         * Get the full file path relative to projectRoot for a class.
         * Constructs path from class internal name and ProtectionDomain
         * location.
         */
        private String getFullFilePath(ClassNode cn, ProtectionDomain protectionDomain) {
            if (cn == null || cn.name == null) {
                return "Unknown.java";
            }

            String sourceFile = cn.sourceFile != null ? cn.sourceFile : simpleName(cn.name) + ".java";

            // Try to get the actual source file path from ProtectionDomain
            if (protectionDomain != null && protectionDomain.getCodeSource() != null
                    && protectionDomain.getCodeSource().getLocation() != null) {
                try {
                    String locationPath = protectionDomain.getCodeSource().getLocation().getPath();
                    if (locationPath != null) {
                        String decodedPath = URLDecoder.decode(locationPath, StandardCharsets.UTF_8.name());
                        // Handle Windows path format from URL
                        if (decodedPath.matches("^/[A-Za-z]:/.*")) {
                            decodedPath = decodedPath.substring(1);
                        }

                        Path classPath = Paths.get(decodedPath).toAbsolutePath().normalize();
                        Path rootPath = Paths.get(projectRoot).toAbsolutePath().normalize();

                        // If classPath is a file (jar), get its parent directory
                        if (classPath.toFile().isFile()) {
                            classPath = classPath.getParent();
                        }

                        // Check if this is within projectRoot
                        if (classPath.startsWith(rootPath)) {
                            try {
                                // Try to find the actual source file by searching common source directories
                                Path actualSourcePath = findActualSourceFile(rootPath, cn.name, sourceFile);
                                if (actualSourcePath != null) {
                                    Path relativeSource = rootPath.relativize(actualSourcePath);
                                    return relativeSource.toString().replace("\\", "/");
                                }

                                // If we can't find the actual file, fall back to inferring from build path
                                // Get relative path from projectRoot
                                Path relative = rootPath.relativize(classPath);
                                String relativeStr = relative.toString().replace("\\", "/");

                                // Determine if it's test or main based on path AND class name
                                // Check for common build output patterns
                                boolean isTestByPath = relativeStr.contains("/test/")
                                        || relativeStr.contains("test-classes")
                                        || relativeStr.contains("test-results");
                                // Also check class name - test classes often have "Test" in name or extend test base classes
                                boolean isTestByName = cn.name != null && (cn.name.contains("Test") || cn.name.endsWith("Test")
                                        || (cn.superName != null && (cn.superName.contains("Test")
                                        || "spock/lang/Specification".equals(cn.superName)
                                        || cn.superName.contains("TestCase"))));
                                // Use class name check as primary indicator, fall back to path if class name doesn't indicate test
                                boolean isTest = isTestByName || isTestByPath;

                                // Extract package path from class internal name
                                // Class name is like "ru/gvsmirnov/sample/SampleJavaClass"
                                String packagePath = cn.name;
                                int lastSlash = packagePath.lastIndexOf('/');
                                if (lastSlash >= 0) {
                                    packagePath = packagePath.substring(0, lastSlash + 1);
                                } else {
                                    packagePath = "";
                                }

                                // Map build output directories to source directories
                                // Common patterns: build/classes/java/main -> src/main/java
                                //                  build/classes/java/test -> src/test/java
                                //                  target/classes -> src/main/java
                                //                  target/test-classes -> src/test/java
                                // Note: Don't assume Groovy files go in groovy directories - they might be in java directories
                                String sourceDir = isTest ? "src/test/java/" : "src/main/java/";

                                return sourceDir + packagePath + sourceFile;
                            } catch (Exception e) {
                                // Fall through to simple construction
                            }
                        }
                    }
                } catch (Exception e) {
                    // Fall through to simple construction
                }
            }

            // Fallback: construct path from class internal name
            // Convert internal name (e.g., "ru/gvsmirnov/sample/SampleJavaClass") to file path
            String packagePath = cn.name;
            // Remove class name from package path
            int lastSlash = packagePath.lastIndexOf('/');
            if (lastSlash >= 0) {
                packagePath = packagePath.substring(0, lastSlash + 1);
            } else {
                packagePath = "";
            }

            // Try to find the actual source file first
            Path actualSourcePath = findActualSourceFile(Paths.get(projectRoot), cn.name, sourceFile);
            if (actualSourcePath != null) {
                Path rootPath = Paths.get(projectRoot).toAbsolutePath().normalize();
                Path relativeSource = rootPath.relativize(actualSourcePath);
                return relativeSource.toString().replace("\\", "/");
            }

            // Fallback: determine if it's test or main source
            // Check if class name contains "Test" or extends common test base classes
            boolean isTest = cn.name != null && (cn.name.contains("Test") || cn.name.endsWith("Test")
                    || (cn.superName != null && (cn.superName.contains("Test")
                    || "spock/lang/Specification".equals(cn.superName)
                    || cn.superName.contains("TestCase"))));

            // Don't assume Groovy files go in groovy directories - use java directories as default
            String sourceDir = isTest ? "src/test/java/" : "src/main/java/";
            return sourceDir + packagePath + sourceFile;
        }

        private void addInt(InsnList il, int value) {
            if (value >= -1 && value <= 5) {
                switch (value) {
                    case -1:
                        il.add(new InsnNode(Opcodes.ICONST_M1));
                        return;
                    case 0:
                        il.add(new InsnNode(Opcodes.ICONST_0));
                        return;
                    case 1:
                        il.add(new InsnNode(Opcodes.ICONST_1));
                        return;
                    case 2:
                        il.add(new InsnNode(Opcodes.ICONST_2));
                        return;
                    case 3:
                        il.add(new InsnNode(Opcodes.ICONST_3));
                        return;
                    case 4:
                        il.add(new InsnNode(Opcodes.ICONST_4));
                        return;
                    case 5:
                        il.add(new InsnNode(Opcodes.ICONST_5));
                        return;
                    default:
                        break;
                }
            }
            il.add(new org.objectweb.asm.tree.LdcInsnNode(value));
        }
    }

    private static void shutdown() {
        try {
            if (coverageFilePid == null || coverageFilePid.isEmpty()) {
                return;
            }
            // Write this JVM's coverage file (per-process file only).
            // Python code will merge all per-process files after all JVMs exit.
            File file = new File(coverageFilePid);
            if (file.getParentFile() != null) {
                file.getParentFile().mkdirs();
            }
            try (PrintWriter out = new PrintWriter(new FileWriter(file, false))) {
                writeCoverageJson(out);
            }
        } catch (IOException ignored) {
        }
    }

    private static void writeCoverageJson(PrintWriter out) {
        // Group statement keys by filename.
        Map<String, List<StatementInfo>> byFile = new LinkedHashMap<>();
        synchronized (statementToTests) {
            for (Map.Entry<String, Set<String>> e : statementToTests.entrySet()) {
                String key = e.getKey();
                String[] parts = key.split(":", 4);
                if (parts.length < 4) {
                    continue;
                }
                String filename = parts[0];
                int line;
                try {
                    line = Integer.parseInt(parts[1]);
                } catch (Exception ex) {
                    continue;
                }
                String className = parts[2];
                String methodName = parts[3];
                Set<String> tests = e.getValue() != null ? new LinkedHashSet<>(e.getValue()) : new LinkedHashSet<>();
                StatementInfo si = new StatementInfo(line, className, methodName, tests);
                byFile.computeIfAbsent(filename, k -> new ArrayList<>()).add(si);
            }
        }

        // Stable ordering for determinism
        for (List<StatementInfo> lst : byFile.values()) {
            lst.sort(Comparator.comparingInt((StatementInfo s) -> s.lineNumber)
                    .thenComparing(s -> s.className)
                    .thenComparing(s -> s.methodName));
        }

        out.print("{\n");
        out.print("  \"files\": {\n");
        boolean firstFile = true;
        for (Map.Entry<String, List<StatementInfo>> entry : byFile.entrySet()) {
            if (!firstFile) {
                out.print(",\n");
            }
            firstFile = false;
            out.print("    \"" + escapeJson(entry.getKey()) + "\": {\n");
            out.print("      \"statements\": [\n");
            List<StatementInfo> stmts = entry.getValue();
            for (int i = 0; i < stmts.size(); i++) {
                StatementInfo st = stmts.get(i);
                if (i > 0) {
                    out.print(",\n");
                }
                out.print("        {\n");
                out.print("          \"line_number\": " + st.lineNumber + ",\n");
                out.print("          \"class_name\": \"" + escapeJson(st.className) + "\",\n");
                out.print("          \"method_name\": \"" + escapeJson(st.methodName) + "\",\n");
                out.print("          \"covered_by_tests\": [");
                List<String> tests = new ArrayList<>(st.tests);
                tests.sort(String::compareTo);
                for (int j = 0; j < tests.size(); j++) {
                    if (j > 0) {
                        out.print(", ");
                    }
                    out.print("\"" + escapeJson(tests.get(j)) + "\"");
                }
                out.print("]\n");
                out.print("        }");
            }
            out.print("\n      ]\n");
            out.print("    }");
        }
        out.print("\n  }\n");
        out.print("}\n");
    }

    private static String escapeJson(String str) {
        if (str == null) {
            return "";
        }
        return str.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    private static class StatementInfo {

        final int lineNumber;
        final String className;
        final String methodName;
        final Set<String> tests;

        StatementInfo(int lineNumber, String className, String methodName, Set<String> tests) {
            this.lineNumber = lineNumber;
            this.className = className != null ? className : "";
            this.methodName = methodName != null ? methodName : "";
            this.tests = tests != null ? tests : new LinkedHashSet<>();
        }
    }
}
