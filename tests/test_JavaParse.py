import base64
import bz2
import unittest

from littledarwin.JavaParse import JavaParse
from antlr4.error.Errors import ParseCancellationException



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

        cls.issue13Code = """
package x;
import java.util.*;

public class SyntaxError {
  public int problemInParadise(int rekTiefe) {
                return missingSemiColon
                
        }
    }
        """

        cls.largeJavaFileBase64Bzipped = b"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"

    def test_parseIssue13(self):
        self.assertRaises(ParseCancellationException, self.javaParse.parse, self.issue13Code)

    def test_largeJavaFile(self):
        LargeJavaFile = bz2.decompress(base64.decodebytes(self.largeJavaFileBase64Bzipped)).decode('utf-8')
        parsedTree = self.javaParse.parse(LargeJavaFile)
        self.assertIsNotNone(parsedTree)

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
        nodeID = \
            parsedTree.children[0].children[1].children[2].children[2].children[2].children[0].children[3].children[
                0].children[3].children[0].children[1].nodeIndex
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
        tree = self.javaParse.parse(
            "class HelloWorld { public static void main( String [] args ) { System.out.println( \"Hello World!\" );  } }")
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
