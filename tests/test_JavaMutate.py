import unittest

from littledarwin.JavaParse import JavaParse
from littledarwin.JavaMutate import *


class TestJavaMutate(unittest.TestCase):
    def setUp(self):
        self.javaParse = JavaParse()
        self.factorialSourceCode = """
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

    public void voidMethod() {
    }
}
"""
        self.traditionalOperatorsSourceCode = """
public class TraditionalOperators {
    public int arithmetic(int a, int b) {
        int c = a + b;
        int d = a - b;
        int e = a * b;
        int f = a / b;
        int g = a % b;
        return c + d + e + f + g;
    }

    public boolean relational(int a, int b) {
        boolean c = a > b;
        boolean d = a >= b;
        boolean e = a < b;
        boolean f = a <= b;
        boolean g = a == b;
        boolean h = a != b;
        return c && d && e && f && g && h;
    }

    public boolean conditional(boolean a, boolean b) {
        return a && b || a;
    }

    public int logical(int a, int b) {
        int c = a & b;
        int d = a | b;
        int e = a ^ b;
        return c & d & e;
    }

    public int assignment(int a, int b) {
        a += b;
        a -= b;
        a *= b;
        a /= b;
        a %= b;
        a &= b;
        a |= b;
        a ^= b;
        a <<= b;
        a >>= b;
        a >>>= b;
        return a;
    }

    public int unary(int a) {
        a++;
        a--;
        ++a;
        --a;
        int b = +a;
        int c = -a;
        boolean d = !true;
        return a;
    }

    public int shift(int a, int b) {
        int c = a << b;
        int d = a >> b;
        int e = a >>> b;
        return c;
    }
}
"""
        self.nullOperatorsSourceCode = """
public class NullOperators {
    public void removeNullCheck(Object a) {
        if (a == null) {
            return;
        }
        if (a != null) {
            return;
        }
    }

    public Object nullifyObjectInitialization() {
        Object a = new Object();
        return a;
    }

    public Object nullifyReturnValue() {
        return new Object();
    }

    public void nullifyInputVariable(Object a) {
    }
}
"""

    def test_RemoveMethod(self):
        tree = self.javaParse.parse(self.factorialSourceCode)
        mutator = RemoveMethod(tree, self.factorialSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 4)

        # main method
        self.assertIn("{\n// void -- no return //\n}", str(mutator.mutants[0]))

        # factorial method
        self.assertIn("return 0;", str(mutator.mutants[1]))
        self.assertIn("return 1;", str(mutator.mutants[2]))

        # voidMethod
        self.assertIn("{\n// void -- no return //\n}", str(mutator.mutants[3]))

    def test_ArithmeticOperatorReplacementBinary(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = ArithmeticOperatorReplacementBinary(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 9)
        replacements = [m.mutationList[0].replacementText for m in mutator.mutants]
        self.assertEqual(replacements.count('-'), 5)
        self.assertEqual(replacements.count('+'), 1)
        self.assertEqual(replacements.count('/'), 2)
        self.assertEqual(replacements.count('*'), 1)

    def test_RelationalOperatorReplacement(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = RelationalOperatorReplacement(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 6)
        self.assertIn("a <= b", str(mutator.mutants[0]))
        self.assertIn("a < b", str(mutator.mutants[1]))
        self.assertIn("a >= b", str(mutator.mutants[2]))
        self.assertIn("a > b", str(mutator.mutants[3]))
        self.assertIn("a != b", str(mutator.mutants[4]))
        self.assertIn("a == b", str(mutator.mutants[5]))

    def test_ConditionalOperatorReplacement(self):
        sourceCode = """
public class ConditionalOperator {
    public boolean conditional(boolean a, boolean b) {
        return a && b || a;
    }
}
"""
        tree = self.javaParse.parse(sourceCode)
        mutator = ConditionalOperatorReplacement(tree, sourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 2)
        replacements = [m.mutationList[0].replacementText for m in mutator.mutants]
        self.assertEqual(replacements.count('||'), 1)
        self.assertEqual(replacements.count('&&'), 1)

    def test_LogicalOperatorReplacement(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = LogicalOperatorReplacement(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 5)
        replacements = [m.mutationList[0].replacementText for m in mutator.mutants]
        self.assertEqual(replacements.count('|'), 3)
        self.assertEqual(replacements.count('^'), 1)
        self.assertEqual(replacements.count('&'), 1)

    def test_AssignmentOperatorReplacementShortcut(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = AssignmentOperatorReplacementShortcut(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 11)
        self.assertIn("a -= b", str(mutator.mutants[0]))
        self.assertIn("a += b", str(mutator.mutants[1]))
        self.assertIn("a /= b", str(mutator.mutants[2]))
        self.assertIn("a *= b", str(mutator.mutants[3]))
        self.assertIn("a /= b", str(mutator.mutants[4]))
        self.assertIn("a |= b", str(mutator.mutants[5]))
        self.assertIn("a ^= b", str(mutator.mutants[6]))
        self.assertIn("a &= b", str(mutator.mutants[7]))
        self.assertIn("a >>= b", str(mutator.mutants[8]))
        self.assertIn("a >>>= b", str(mutator.mutants[9]))
        self.assertIn("a >>= b", str(mutator.mutants[10]))

    def test_ArithmeticOperatorReplacementUnary(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = ArithmeticOperatorReplacementUnary(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 2)
        self.assertIn("-a", str(mutator.mutants[0]))
        self.assertIn("+a", str(mutator.mutants[1]))

    def test_ConditionalOperatorDeletion(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = ConditionalOperatorDeletion(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 1)
        self.assertIn(" true", str(mutator.mutants[0]))

    def test_ShiftOperatorReplacement(self):
        tree = self.javaParse.parse(self.traditionalOperatorsSourceCode)
        mutator = ShiftOperatorReplacement(tree, self.traditionalOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 3)
        self.assertIn("a >> b", str(mutator.mutants[0]))
        self.assertIn("a << b", str(mutator.mutants[1]))
        self.assertIn("a >> b", str(mutator.mutants[2]))

    def test_RemoveNullCheck(self):
        tree = self.javaParse.parse(self.nullOperatorsSourceCode)
        mutator = RemoveNullCheck(tree, self.nullOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 2)
        self.assertIn("true", str(mutator.mutants[0]))
        self.assertIn("false", str(mutator.mutants[1]))

    def test_NullifyObjectInitialization(self):
        tree = self.javaParse.parse(self.nullOperatorsSourceCode)
        mutator = NullifyObjectInitialization(tree, self.nullOperatorsSourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 2)
        self.assertIn("= null", str(mutator.mutants[0]))

    def test_NullifyReturnValue(self):
        sourceCode = """
public class NullifyReturnValue {
    public Object nullifyReturnValue() {
        return new Object();
    }
}
"""
        tree = self.javaParse.parse(sourceCode)
        mutator = NullifyReturnValue(tree, sourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 1)
        self.assertIn("return null;", str(mutator.mutants[0]))

    def test_NullifyInputVariable(self):
        sourceCode = """
public class NullifyInputVariable {
    public void nullifyInputVariable(Object a) {
    }
}
"""
        tree = self.javaParse.parse(sourceCode)
        mutator = NullifyInputVariable(tree, sourceCode, self.javaParse)
        self.assertEqual(len(mutator.mutants), 1)
        self.assertIn("a = null;", str(mutator.mutants[0]))


if __name__ == '__main__':
    unittest.main()
