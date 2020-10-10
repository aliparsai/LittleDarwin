import unittest
from littledarwin.JavaParse import JavaParse


class TestJavaParse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.javaParse = JavaParse()

        cls.factorialSourceCode = """
public class Factorial {
    public static void main(String[] args) {
        final int NUM_FACTS = 100;
        for(int i = 0; i < NUM_FACTS; i++)
            System.out.println( i + "! is " + factorial(i) );
        }

    public static int factorial(int n) {
         int result = 1;
         for(int i = 2; i <= n; i++)
            result *= i;
         return result; 
    }
}
"""
        cls.emptyInterfaceSourceCode = """
import java.lang.*;
public interface EmptyInterface {}
"""

        cls.methodTypesSourceCode = """
import java.lang.*;
public class VariousMethodTypes {
    public static void main(String[] args) {
    
    }

    private void voidMethod() {
    String result = "NULL";
    }
    
    private int intMethod(int n) {
         int result = 1;
         return result; 
    }
    
    private byte byteMethod(int n) {
         byte result = 1;
         return result; 
    }

    private short shortMethod(int n) {
         short result = 1;
         return result; 
    }

    private long longMethod(int n) {
         long result = 1;
         return result; 
    }
    
    
    public boolean boolMethod() {
         boolean result = true;
         return result; 
    }

    public float floatMethod() {
         float result = 0.1;
         return result; 
    }

    private double doubleMethod() {
         double result = 0.1;
         return result; 
    }
    
    private char charMethod() {
         char result = "A";
         return result; 
    }
    
    private String stringMethod() {
         String result = "Say Hello To My Little FRIEND!!!";
         return result; 
    }
    
    public Object objectMethod() {
         Object result = new Object();
         return result;
    }
    
    private T[] typeArrayMethod(T[] t) {
         T[] result = t;
         return result; 
    }
    
    
}


"""

        cls.java7SourceCode = """
// Source: https://en.wikipedia.org/wiki/Java_syntax
// Source: https://docs.oracle.com/javase/tutorial/java/nutsandbolts/index.html

/* This is a multi-line comment.
It may occupy more than one line. */

// This is an end-of-line comment

/**
 * This is a documentation comment.
 * 
 * @author John Doe
 */

package myapplication.mylibrary;

import java.util.Random; // Single type declaration
import java.util.*;
import java.*;
import static java.lang.System.out; //'out' is a static field in java.lang.System
import static screen.ColorName.*;

public enum ColorName {
    RED, BLUE, GREEN
};

// See http://docs.oracle.com/javase/7/docs/technotes/guides/language/underscores-literals.html
public class LexerTest {
    static void main(String[] args) {
        long creditCardNumber = 1234_5678_9012_3456L;
        long socialSecurityNumber = 999_99_9999L;
        float pi = 3.14_15F;
        long hexBytes = 0xFF_EC_DE_5E;
        long hexWords = 0xCAFE_BABE;
        long maxLong = 0x7fff_ffff_ffff_ffffL;
        byte nybbles = 0b0010_0101;
        long bytes = 0b11010010_01101001_10010100_10010010;
        long lastReceivedMessageId = 0L;
        double hexDouble1 = 0x1.0p0;
        double hexDouble2 = 0x1.956ad0aae33a4p117;
        int octal = 01234567;
        long hexUpper = 0x1234567890ABCDEFL;
        long hexLower = 0x1234567890abcedfl;

        int x1 = _52;              // This is an identifier, not a numeric literal
        int x2 = 5_2;              // OK (decimal literal)
        int x4 = 5_______2;        // OK (decimal literal)

        int x7 = 0x5_2;            // OK (hexadecimal literal)

        int x9 = 0_52;             // OK (octal literal)
        int x10 = 05_2;            // OK (octal literal)

        int x, y, result;

        // Arithmetic operators
        result = x + y;
        result = x - y;
        result = x * y;
        result = y / x;
        result = x % 3;

        // Unary operators
        result = +x;
        result = -y;
        result = ++x;
        result = --y;
        boolean ok = false;
        boolean not_ok = !ok;

        // assignments yield a value
        (result = System.class).getName();

        // Prefix & postfix
        ++x;
        x++;
        --y;
        y--;
        LexerTest.prePost++;
        LexerTest.prePost--;
        myapplication.mylibrary.LexerTest.prePost++;
        myapplication.mylibrary.LexerTest.prePost--;
        this.prePost++;
        this.prePost--;
        super.prePost++;
        super.prePost--;
        someMethod()[0]++;
        someMethod()[0]--;

        ++LexerTest.prePost;
        --LexerTest.prePost;
        ++myapplication.mylibrary.LexerTest.prePost;
        --myapplication.mylibrary.LexerTest.prePost;
        ++this.prePost;
        --this.prePost;
        ++super.prePost;
        --super.prePost;
        ++someMethod()[0];
        --someMethod()[0];

        // Relational operators
        result = x == y;
        result = x != y;
        result = x > y;
        result = x >= y;
        result = x < y;
        result = x <= y;

        // Conditional operators
        if ((x > 8) && (y > 8)) {
        }

        if ((x > 10) || (y > 10)) {
        }

        result = (x > 10) ? x : y;

        // Ternary operator right associativity
        int f =  b1 ? b2 : b3 ? 3 : 4;

        // Bitwise and Bit shift operators
        result = ~x;
        result = x << 1;
        result = x >> 2;
        result = x >>> 3;
        result = x & 4;
        result = x ^ 5;
        result = x | 6;

        // Assignment operators
        result = x;
        result += x;
        result -= x;
        result *= x;
        result /= x;
        result %= x;
        result &= x;
        result ^= x;
        result |= x;
        result <<= x;
        result >>= x;
        result >>>= x;
    }

    public static void methodCalls() {
        new Object().getClass().hashCode();
        new String[] { "test" }[0].getLength();
        String[] strings;
        (strings = new String[] {"test"})[0].charAt(0);
        strings[0].length();
        Foo foo = new Foo().new Bar();
        foo.hashCode();
        Foo.class.hashCode();
        new HashMap<Object, String>(5).get(null);
    }
}

public class ImportsTest {
    public static void main(String[] args) {
        /* The following line is equivalent to
         * java.util.Random random = new java.util.Random();
         * It would've been incorrect without the import declaration */
        Random random = new Random();
    }
}

public class HelloWorld {
    public static void main(String[] args) {
        /* The following line is equivalent to:
           System.out.println("Hello World!");
           and would have been incorrect without the import declaration. */
        out.println("Hello World!");

        // Conditional statements -------------------
        if (i == 3) doSomething();

        if (i == 2) {
            doSomething();
        } else {
            doSomethingElse();
        }

        if (i == 3) {
            doSomething();
        } else if (i == 2) {
            doSomethingElse();
        } else {
            doSomethingDifferent();
        }

        int a = 1;
        int b = 2;
        int minVal = (a < b) ? a : b;

        // switch
        switch (ch) {
            case 'A':
                doSomething(); // Triggered if ch == 'A'
                break;
            case 'B':
            case 'C':
                doSomethingElse(); // Triggered if ch == 'B' or ch == 'C'
                break;
            default:
                doSomethingDifferent(); // Triggered in any other case
                break;
        }

        // Iteration statements -------------------
        while (i < 10) {
            doSomething();
        }

        do {
            doSomething();
        } while (i < 10);

        for (int i = 0; i < 10; i++) {
            doSomething();
        }

        // A more complex loop using two variables
        for (int i = 0, j = 9; i < 10; i++, j -= 3) {
            doSomething();
        }

        for (;;) {
            doSomething();
        }

        for (int i : intArray) {
            doSomething(i);
        }

        // Jump statements -------------------
        // Label
        start:
            someMethod();

        // break
        for (int i = 0; i < 10; i++) {
            while (true) {
                break;
            }
            // Will break to this point
        }

        outer:
            for (int i = 0; i < 10; i++) {
                while (true) {
                    break outer;
                }
            }
            // Will break to this point

        // continue
        int ch;
        while (ch = getChar()) {
            if (ch == ' ') {
                continue; // Skips the rest of the while-loop
            }

            // Rest of the while-loop, will not be reached if ch == ' '
            doSomething();
        }

        outer:
        for (String str : stringsArr) {
            char[] strChars = str.toCharArray();
            for (char ch : strChars) {
                if (ch == ' ') {
                    /* Continues the outer cycle and the next
                    string is retrieved from stringsArr */
                    continue outer;
                }
                doSomething(ch);
            }
        }

        // return
        // If streamClosed is true, execution is stopped
        if (streamClosed) {
            return;
        }
        readFromStream();

        int result = a + b;
        return result;

        // Exception handling statements -------------------
        // try-catch-finally
        try {
            // Statements that may throw exceptions
            methodThrowingExceptions();
        } catch (Exception ex) {
            // Exception caught and handled here
            reportException(ex);
        } finally {
            // Statements always executed after the try/catch blocks
            freeResources();
        }

        try {
            methodThrowingExceptions();
        } catch (IOException | IllegalArgumentException ex) {
            //Both IOException and IllegalArgumentException will be caught and handled here
            reportException(ex);
        }

        // try-with-resources statement
        try (FileOutputStream fos = new FileOutputStream("filename");
            XMLEncoder xEnc = new XMLEncoder(fos))
        {
            xEnc.writeObject(object);
        } catch (IOException ex) {
            Logger.getLogger(Serializer.class.getName()).log(Level.SEVERE, null, ex);
        }

        // throw
        if (obj == null) {
            // Throws exception of NullPointerException type
            throw new NullPointerException();
        }
        // Will not be called, if object is null
        doSomethingWithObject(obj);

        // Thread concurrency control -------------------
        /* Acquires lock on someObject. It must be of a reference type and must be non-null */
        synchronized (someObject) {
            // Synchronized statements
        }

        // assert statement
        // If n equals 0, AssertionError is thrown
        assert n != 0;
        /* If n equals 0, AssertionError will be thrown
        with the message after the colon */
        assert n != 0 : "n was equal to zero";

        // Reference types -------------------
        // Arrays
        int[] numbers = new int[5];
        numbers[0] = 2;
        int x = numbers[0];

        // Initializers -------------------
        // Long syntax
        int[] numbers = new int[] {20, 1, 42, 15, 34};
        // Short syntax
        int[] numbers2 = {20, 1, 42, 15, 34};

        // Multi-dimensional arrays
        int[][] numbers = new int[3][3];
        numbers[1][2] = 2;
        int[][] numbers2 = {{2, 3, 2}, {1, 2, 6}, {2, 4, 5}};

        int[][] numbers = new int[2][]; //Initialization of the first dimension only
        numbers[0] = new int[3];
        numbers[1] = new int[2];

        // Prefix & postfix
        numbers[0][0]++;
        numbers[0][0]--;
        ++numbers[0][0];
        --numbers[0][0];
        foo()[0]++;
        foo()[0]--;
        ++foo()[0];
        --foo()[0];
    }
}

// Classes -------------------
// Top-level class 
class Foo {
    // Class members
}

// Inner class
class Foo { // Top-level class
    class Bar { // Inner class
    }

    static void inner_class_constructor() {
        // https://docs.oracle.com/javase/specs/jls/se9/html/jls-15.html#jls-15.9
        Foo foo = new Foo();
        Foo.Bar fooBar1 = foo.new Bar();
        Foo.Bar fooBar2 = new Foo().new Bar();
    }
}

// Nested class
class Foo { // Top-level class
    static class Bar { // Nested class
    }
}

// Local class
class Foo {
    void bar() {
        @WeakOuter
        class Foobar {// Local class within a method
        }
    }
}

// Anonymous class
class Foo {
    void bar() {

        new Object() {// Creation of a new anonymous class extending Object
        };
    }
}

// Access modifiers
public class Foo {
    int go() {
        return 0;
    }

    private class Bar {
    }
}

// Constructors and initializers
class Foo {
    String str;

    Foo() { // Constructor with no arguments
        // Initialization
    }

    Foo(String str) { // Constructor with one argument
        this.str = str;
    }
}

class Foo {
    static {
        // Initialization
    }
}

class Foo {
    {
        // Initialization
    }
}

// Methods -------------------
class Foo {
    public Foo() {
        System.out.println(Foo.class.getName() + ": constructor runtime");
    }
    public Foo(int a, int b) {
        System.out.println(Foo.class.getName() + ": overloaded constructor " + this());
    }
    int bar(int a, int b) {
        return (a*2) + b;
    }

    /* Overloaded method with the same name but different set of arguments */
    int bar(int a) {
        return a*2;
    }

    void openStream() throws IOException, myException { // Indicates that IOException may be thrown
    }

    // Varargs
    void printReport(String header, int... numbers) { //numbers represents varargs
        System.out.println(header);
        for (int num : numbers) {
            System.out.println(num);
        }
    }
}

// Overriding methods
class Operation {
    public int doSomething() {
        return 0;
    }
}

class NewOperation extends Operation {
    @Override
    public int doSomething() {
        return 1;
    }
}

// Abstract classes
public class AbstractClass {
    private static final String hello;

    static {
        System.out.println(AbstractClass.class.getName() + ": static block runtime");
        hello = "hello from " + AbstractClass.class.getName();
    }

    {
        System.out.println(AbstractClass.class.getName() + ": instance block runtime");
    }

    public AbstractClass() {
        System.out.println(AbstractClass.class.getName() + ": constructor runtime");
    }

    public static void hello() {
        System.out.println(hello);
    }
}

public class CustomClass extends AbstractClass {

    static {
        System.out.println(CustomClass.class.getName() + ": static block runtime");
    }

    {
        System.out.println(CustomClass.class.getName() + ": instance block runtime");
    }

    public CustomClass() {
        super();
        System.out.println(CustomClass.class.getName() + ": constructor runtime");
    }

    public static void main(String[] args) {
        CustomClass nc = new CustomClass();
        hello();
        AbstractClass.hello();//also valid
    }
}

// Enumerations -------------------
enum Season {
    WINTER, SPRING, SUMMER, AUTUMN
}

public enum Season {
    WINTER("Cold"), SPRING("Warmer"), SUMMER("Hot"), AUTUMN("Cooler");

    Season(String description) {
        this.description = description;
    }

    private final String description;

    public String getDescription() {
        return description;
    }
}

public enum Season {
    WINTER {
        String getDescription() {return "cold";}
    },
    SPRING {
        String getDescription() {return "warmer";}
    },
    SUMMER {
        String getDescription() {return "hot";}
    },
    FALL {
        String getDescription() {return "cooler";}
    };
}

// Interfaces -------------------
interface ActionListener {
    int ACTION_ADD = 0;
    int ACTION_REMOVE = 1;

    void actionSelected(int action);
}

interface RequestListener {
    int requestReceived();
}

class ActionHandler implements ActionListener, RequestListener {
    public void actionSelected(int action) {
    }

    public int requestReceived() {
    }
}

class Dummy {
    public void dummy() {
        //Calling method defined by interface
        RequestListener listener = new ActionHandler(); /*ActionHandler can be
                                           represented as RequestListener...*/
        listener.requestReceived(); /*...and thus is known to implement
                                    requestReceived() method*/
    }
}

class Dummy {
    public void dummy() {
        interface AnotherInterface extends Runnable { // local interface
            void work();
        }
    }
}

// Annotations  -------------------
@interface BlockingOperations {
}

@interface BlockingOperations {
    boolean fileSystemOperations();
    boolean networkOperations() default false;
}

class Dummy {
    @BlockingOperations(/*mandatory*/ fileSystemOperations = true,
    /*optional*/ networkOperations = true)
    void openOutputStream() { //Annotated method
    }

    @Unused // Shorthand for @Unused()
    void travelToJupiter() {
    }
}

// Generics -------------------
// Generic classes
/* This class has two type variables, T and V. T must be 
a subtype of ArrayList and implement Formattable interface */
public class Mapper<T extends ArrayList & Formattable, V> {
    public void add(T array, V item) {
        // array has add method because it is an ArrayList subclass
        array.add(item);

        /* Mapper is created with CustomList as T and Integer as V.
        CustomList must be a subclass of ArrayList and implement Formattable */
        Mapper<CustomList, Integer> mapper = new Mapper<CustomList, Integer>();

        Mapper<CustomList, ?> mapper;
        mapper = new Mapper<CustomList, Boolean>();
        mapper = new Mapper<CustomList, Integer>();
    }
}

// Generic methods and constructors -------------------
class Mapper {
    // The class itself is not generic, the constructor is
    <T, V> Mapper(T array, V item) {
    }

    /* This method will accept only arrays of the same type as
    the searched item type or its subtype*/
    static <T, V extends T> boolean contains(T item, V[] arr) {
        for (T currentItem : arr) {
            if (item.equals(currentItem)) {
                return true;
            }
        }
        return false;
    }
}

interface Expandable<T extends Number> {
    void addItem(T item);
}

// This class is parameterized
class Array<T extends Number> implements Expandable<T> {
    void addItem(T item) {
    }
}

// And this is not and uses an explicit type instead
class IntegerArray implements Expandable<Integer> {
    void addItem(Integer item) {
    }
}

// Annotation type definition
public @interface Bean {
    public static final String ASDF = "ASDF";
}
"""
        cls.java8SourceCode = """
// Source: https://en.wikipedia.org/wiki/Java_syntax
// Source: https://docs.oracle.com/javase/tutorial/java/nutsandbolts/index.html

// Lambdas
public class Lambdas {
     public static void main(String[] args) {
        // use predicate composition to remove matching names
        List<Name> list = new ArrayList<>();
        for (Name name : NAMES) {
            list.add(name);
        }
        Predicate<Name> pred1 = name -> "Sally".equals(name.firstName);
        Predicate<Name> pred2 = name -> "Queue".equals(name.lastName);
        list.removeIf(pred1.or(pred2));
        printNames("Names filtered by predicate:", list.toArray(new Name[list.size()]));

        Comparator<Name> com1 = Comparator.comparing((Name name1) -> name1.lastName)
            .thenComparing(name2 -> name2.firstName);
        Comparator<Name> com2 = Comparator.<Name,String>comparing(name1 -> name1.lastName)
            .thenComparing(name2 -> name2.firstName);

        // sort array using lambda expression
        copy = Arrays.copyOf(NAMES, NAMES.length);
        Arrays.sort(copy, (a, b) -> a.compareTo(b));
        printNames("Names sorted with lambda expression:", copy);
     }
}

// Default interface method
interface Formula {
    double calculate(int a);
    
    default double sqrt(int a) {
        return Math.sqrt(a);
    }
}

// Double colon
public class For {
    public void bar() {
        Function<Computer, Integer> getAge = Computer::getAge;
        Integer computerAge = getAge.apply(c1);

        Function<Computer, Integer> getAgeAlt = this::getAge;
        Function<Computer, Integer> getAgeAlt2 = MyClass.this::getAge;
        Function<Computer, Integer> getAgeAlt3 = generate()::getAge;
        Function<Computer, Integer> getAgeAlt4 = MyClass.generate()::getAge;
        Function<Computer, Integer> getAgeAlt5 = MyClass.twice().nested()::getAge;
        Function<Computer, Integer> getAgeAlt6 = twice().nested()::getAge;
        Function<Computer, Integer> getAgeAlt7 = this.singletonInstanceMethod::get;

        autodetect(this.beans, ((AutodetectCapableMBeanInfoAssembler) this.assembler)::includeBean);

        TriFunction <Integer, String, Integer, Computer> c6Function = Computer::new;
        Computer c3 = c6Function.apply(2008, "black", 90);

        Function <Integer, Computer[]> computerCreator = Computer[]::new;
        Computer[] computerArray = computerCreator.apply(5);
    }
}

// Type Annotations
public class Annotations {
    @Valid
    private List<@NotNull String> property;
}

public interface CallableProcessingInterceptor {
    default <T> void beforeConcurrentHandling(NativeWebRequest request, Callable<T> task) throws Exception {
    }
}

@FunctionalInterface
public interface RouterFunction<T extends ServerResponse> {
    default <S extends ServerResponse> RouterFunction<S> filter(HandlerFilterFunction<T, S> filterFunction) {
        return new RouterFunctions.FilteredRouterFunction<>(this, filterFunction);
    }
}

// Unicode
class Unicode {
    public static void main(String[] args) {
        System.out.println("A = \\uuu0041");
    }
}
        
        
"""
        cls.manyStringsSourceCode = """
class Test
{
    @ApiModelProperty(value =
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +

        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +

        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +

        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +

        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +

        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" +
        "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x" + "x"
    )
    @XmlElement
    protected AdditionalParams additionalParams;
}
 """
        cls.java9SourceCode = """
package open.module.module;

import java.module.moduleTest;
import java.open.openTest;


module com.example.foo {
 requires com.example.foo.http;
 requires java.logging;
 requires transitive com.example.foo.network;
 exports com.example.foo.bar;
 exports com.example.foo.internal to com.example.foo.probe;
 opens com.example.foo.quux;
 opens com.example.foo.internal to com.example.foo.network,
 com.example.foo.probe;
 uses com.example.foo.spi.Intf;
 provides com.example.foo.spi.Intf with com.example.foo.Impl;
}


public class HelloWorld { 
   public static void main(String[] args) { 
      System.out.println("Hello, World");
   }
}


class module {
 java.module.moduleTest module(){
  return module();
 }
}
class open {
 java.module.moduleTest module(){
  return module();
 }
}

public class to {
 to with = null;
  public to to() {
   return with.to();
  }
  public to to() {
   to exports = null;
   to provides = null;
   to requires = null;
   to uses = null;
   return to();
  }

}

public class TryWithResourceDemo implements AutoCloseable{
 public static void main(String[] args){
  TryWithResourceDemo demo=new TryWithResourceDemo();
  try(demo){demo.doSomething();}
  /* Prior to Java 9, you should write something like
   try(TryWithResourceDemo demo=new TryWithResourceDemo()){demo.doSomething();}
  */
 }
 public void doSomething(){
  System.out.println("Hello world!");
 }
 @Override
 public void close(){
  System.out.println("I am going to be closed");
 }
}
"""

    def test_parseJava7(self):
        parsedTree = self.javaParse.parse(self.java7SourceCode)
        self.assertIsNotNone(parsedTree)

    def test_parseJava8(self):
        parsedTree = self.javaParse.parse(self.java8SourceCode)
        self.assertIsNotNone(parsedTree)

    def test_parseMethodTypes(self):
        parsedTree = self.javaParse.parse(self.methodTypesSourceCode)
        self.assertIsNotNone(parsedTree)

    # def test_parseJava9(self):
    #     parsedTree = self.javaParse.parse(self.java9SourceCode)

    ## Too slow
    # def test_parseManyStrings(self):
    #     parsedTree = self.javaParse.parse(self.manyStringsSourceCode)
    #

    def test_getMethodNameForNode(self):
        parsedTree = self.javaParse.parse(self.factorialSourceCode)
        nodeID = parsedTree.children[0].children[1].children[2].children[2].children[2].children[0].children[3].children[0].children[3].children[0].children[1].nodeIndex
        methodName = self.javaParse.getMethodNameForNode(parsedTree, nodeID)

        self.assertIn('factorial', methodName)
        self.assertEqual("***not in a method***", self.javaParse.getMethodNameForNode(parsedTree, 3))

    def test_getCyclomaticComplexity(self):
        parsedTree = self.javaParse.parse(self.factorialSourceCode)
        cyclomaticComplexityDict = self.javaParse.getCyclomaticComplexityAllMethods(parsedTree)

        for key in cyclomaticComplexityDict.keys():
            if "main" in key:
                keyMain = key
            if "factorial" in key:
                keyFactorial = key

        self.assertEqual(len(cyclomaticComplexityDict), 2)
        self.assertEqual(cyclomaticComplexityDict[keyMain], 2)
        self.assertEqual(cyclomaticComplexityDict[keyFactorial], 2)

    def test_getMethodRanges(self):
        parsedTree = self.javaParse.parse(self.factorialSourceCode)
        methodRanges = self.javaParse.getMethodRanges(parsedTree)

        for key in methodRanges.keys():
            if "main" in key:
                keyMain = key
            if "factorial" in key:
                keyFactorial = key

        self.assertEqual(len(methodRanges), 2)
        self.assertEqual(methodRanges[keyMain], (69, 219))
        self.assertEqual(methodRanges[keyFactorial], (261, 379))

    def test_numerifyHelloWorld(self):
        tree = self.javaParse.parse("class HelloWorld { public static void main( String [] args ) { System.out.println( \"Hello World!\" );  } }")
        self.javaParse.numerify(tree)

        nodeStack = [tree]
        while len(nodeStack) > 0:
            node = nodeStack.pop()
            self.assertTrue(hasattr(node, 'nodeIndex'))
            nodeStack.extend(getattr(node, 'children', []))

    def test_numerifyEmptyTree(self):
        tree = self.javaParse.parse("")
        self.javaParse.numerify(tree)

        nodeStack = [tree]
        while len(nodeStack) > 0:
            node = nodeStack.pop()
            self.assertTrue(hasattr(node, 'nodeIndex'))
            nodeStack.extend(getattr(node, 'children', []))

    def test_numerifyWrongTree(self):
        tree = ['This is the wrong type for a tree']
        try:
            self.javaParse.numerify(tree)
            raise ValueError

        except ValueError as e:
            self.fail("Expected exception was not raised.")

        except AssertionError as e:
            # it's all good!
            self.assertTrue(True)
