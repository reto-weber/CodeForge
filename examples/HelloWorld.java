public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World from Java!");
        System.out.println("========================");
        System.out.println();

        // Variables and basic operations
        int a = 10, b = 5;
        System.out.println("Numbers: a = " + a + ", b = " + b);
        System.out.println("a + b = " + (a + b));
        System.out.println("a - b = " + (a - b));
        System.out.println("a * b = " + (a * b));
        System.out.println("a / b = " + (a / b));

        // String operations
        String greeting = "Welcome to Java programming!";
        System.out.println("\nString: " + greeting);
        System.out.println("String length: " + greeting.length());

        // Array demonstration
        int[] numbers = { 1, 2, 3, 4, 5 };
        System.out.print("\nArray contents: ");
        for (int num : numbers) {
            System.out.print(num + " ");
        }
        System.out.println();

        // Object creation
        String language = "Java";
        System.out.println("\nProgramming language: " + language.toUpperCase());
    }
}
