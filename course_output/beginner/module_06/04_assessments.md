# Debugging and Development Tools for MCP Assessment

**Instructions:** Please answer all questions to the best of your ability. Show your work or provide detailed explanations where requested.

---

### Section 1: Multiple Choice Questions

Choose the best answer for each question.

1.  Which of the following is the primary Integrated Development Environment (IDE) used for developing applications for Microchip PIC microcontrollers?
    a) Arduino IDE
    b) Keil uVision
    c) MPLAB X IDE
    d) Eclipse

2.  What is the main purpose of an In-Circuit Debugger (ICD) like the PICkit 4 or ICD 5?
    a) To permanently program a microcontroller without debugging capabilities.
    b) To simulate microcontroller behavior on a PC without hardware.
    c) To allow real-time debugging of code running on a physical microcontroller.
    d) To measure voltage and current on a circuit board.

3.  Which debugging command allows you to execute the current line of code and then pause at the next line, stepping *over* any function calls without entering them?
    a) Step Into
    b) Step Over
    c) Step Out
    d) Run to Cursor

4.  In MPLAB X IDE, which window is typically used to view the current values of variables, registers, and memory locations during a debugging session?
    a) Project Explorer
    b) Output Window
    c) Watch Window / Variables Window
    d) Call Stack Window

5.  A "hardware breakpoint" is distinct from a "software breakpoint" primarily because:
    a) It can only be set in assembly code.
    b) It requires specific hardware support from the microcontroller and debugger.
    c) It is set by modifying the program's source code.
    d) It can only be used with a simulator.

---

### Section 2: Short Answer and Explanation Questions

Provide concise and clear answers to the following questions.

6.  **Differentiate between a Microchip Simulator and an In-Circuit Debugger (ICD).**
    Explain when you would typically choose to use one over the other in your development process.

7.  **Explain the purpose of the "Call Stack" window during a debugging session.**
    How can it help you diagnose issues in your code?

8.  **Describe the steps you would take in MPLAB X IDE to set a breakpoint and inspect a variable's value when that breakpoint is hit.**

9.  **When might you need to use an external tool like a Logic Analyzer or an Oscilloscope in conjunction with your MPLAB X IDE debugger for an MCP project?**
    Provide at least one specific scenario for each tool.

10. **Briefly explain the role of the compiler (e.g., XC8, XC16, XC32) and the linker in the Microchip development toolchain.**

---

### Section 3: Scenario-Based Question

Apply your knowledge to solve the following problem.

11. **Debugging Scenario: LED Not Blinking**
    You have written a simple C program for a PIC microcontroller to blink an LED connected to RA0 every 500ms. After programming the PIC, the LED remains constantly ON. You are using MPLAB X IDE with a PICkit 4 debugger.

    **Your Task:** Outline a step-by-step debugging strategy using the tools available in MPLAB X IDE and your PICkit 4 to identify why the LED is not blinking. Be specific about which debugging features you would use and why.

---

### Answer Key

### Section 1: Multiple Choice Questions

1.  **c) MPLAB X IDE**
2.  **c) To allow real-time debugging of code running on a physical microcontroller.**
3.  **b) Step Over**
4.  **c) Watch Window / Variables Window**
5.  **b) It requires specific hardware support from the microcontroller and debugger.**

---

### Section 2: Short Answer and Explanation Questions

6.  **Differentiate between a Microchip Simulator and an In-Circuit Debugger (ICD).**
    *   **Microchip Simulator:** A software-based tool within MPLAB X IDE that emulates the behavior of a specific PIC microcontroller on your computer. It does not require physical hardware.
    *   **In-Circuit Debugger (ICD):** A hardware device (e.g., PICkit 4, ICD 5) that connects your computer to a physical PIC microcontroller on your target board. It allows you to run, pause, step through code, and inspect variables on the actual hardware in real-time.

    **When to use:**
    *   **Simulator:** Ideal for initial code development, testing algorithms, verifying logic, and debugging code without needing physical hardware. It's useful for early-stage development or when hardware is not yet available.
    *   **ICD:** Essential for debugging issues that are hardware-dependent, such as timing problems, peripheral interactions (e.g., ADC, SPI, I2C), power consumption, or when the simulator cannot accurately replicate real-world conditions. It's used when you need to verify code behavior on the actual target system.

7.  **Explain the purpose of the "Call Stack" window during a debugging session.**
    The "Call Stack" window displays the sequence of function calls that led to the current point of execution in your program. Each entry in the stack represents a function that has been called but has not yet returned.

    **How it helps diagnose issues:**
    *   **Tracing Program Flow:** It allows you to see the path your program took to reach a specific line of code, which is crucial for understanding how control flows through different functions.
    *   **Identifying Infinite Recursion/Stack Overflow:** If the call stack grows excessively large, it can indicate an infinite recursion or a stack overflow issue.
    *   **Understanding Context:** By examining the call stack, you can understand the context in which a function was called, including the arguments passed and the local variables of the calling functions (by navigating up the stack). This helps in debugging issues related to incorrect function calls or data propagation.

8.  **Describe the steps you would take in MPLAB X IDE to set a breakpoint and inspect a variable's value when that breakpoint is hit.**
    1.  **Open the Source File:** Navigate to the C or assembly source file where you want to set the breakpoint.
    2.  **Set Breakpoint:** Click in the left margin (gutter) next to the line of code where you want the program to pause. A red square will appear, indicating a breakpoint.
    3.  **Start Debugging Session:** Click the "Debug Project" button (usually a green arrow with a bug icon) in the MPLAB X IDE toolbar. This will compile the code, program the microcontroller, and start the debugging session.
    4.  **Program Execution Pauses:** When the program execution reaches the line with the breakpoint, it will pause, and the line will be highlighted.
    5.  **Inspect Variable:**
        *   **Hover:** Hover your mouse cursor over the variable name in the source code. A tooltip will often pop up showing its current value.
        *   **Watch Window:** Open the "Watch" window (Window -> Debugging -> Watches). Click the "New Watch" button or type the variable name into an empty row and press Enter. The Watch window will continuously display the variable's value as you step through the code.
        *   **Variables Window:** Open the "Variables" window (Window -> Debugging -> Variables). This window automatically displays local variables in the current scope.

9.  **When might you need to use an external tool like a Logic Analyzer or an Oscilloscope in conjunction with your MPLAB X IDE debugger for an MCP project?**

    *   **Logic Analyzer:**
        *   **Scenario:** Debugging communication protocols like SPI, I2C, UART, or parallel bus interfaces where you need to observe the timing and sequence of multiple digital signals simultaneously. For example, if your SPI communication isn't working, a logic analyzer can show if the clock (SCK), data in (MISO), data out (MOSI), and chip select (SS) lines are toggling correctly and in the right order, and if the data bits are what you expect.
        *   **Why:** The IDE debugger can tell you what your code *thinks* it's sending, but a logic analyzer shows what's *actually* happening on the pins, revealing issues like incorrect clock polarity, phase, or data corruption due to timing mismatches.

    *   **Oscilloscope:**
        *   **Scenario:** Debugging analog signals, power supply issues, noise problems, or precise timing measurements of single or a few signals. For example, if an ADC reading is erratic, an oscilloscope can show if the analog input signal is stable, noisy, or within the expected voltage range. Another example is verifying the frequency and duty cycle of a PWM output.
        *   **Why:** An oscilloscope provides a visual representation of voltage over time, allowing you to see signal integrity, rise/fall times, glitches, noise, and precise timing relationships that a digital-only logic analyzer or the IDE debugger cannot reveal.

10. **Briefly explain the role of the compiler (e.g., XC8, XC16, XC32) and the linker in the Microchip development toolchain.**

    *   **Compiler (e.g., XC8, XC16, XC32):** The compiler's role is to translate human-readable source code (e.g., C code) into machine-readable object code. It checks for syntax errors, performs optimizations, and generates an object file (`.o` or `.obj`) for each source file. Each XC compiler is specific to a family of PIC microcontrollers (e.g., XC8 for 8-bit PICs, XC16 for 16-bit PICs, XC32 for 32-bit PICs).

    *   **Linker:** The linker's role is to combine all the object files generated by the compiler (and any pre-compiled library files) into a single, executable firmware image (e.g., a `.hex` file). It resolves references between different object files (e.g., function calls from one file to another), allocates memory addresses for code and data, and ensures that all necessary components are present and correctly linked to form a complete program that can be loaded onto the microcontroller.

---

### Section 3: Scenario-Based Question

11. **Debugging Scenario: LED Not Blinking**

    **Debugging Strategy:**

    1.  **Initial Check (Sanity Check):**
        *   **Verify Hardware:** Double-check the LED connection (polarity, series resistor), power supply to the PIC, and ensure the PICkit 4 is properly connected and recognized by MPLAB X IDE.
        *   **Verify Configuration Bits:** In MPLAB X IDE, go to `Window -> PIC Memory Views -> Configuration Bits`. Ensure that the oscillator settings, watchdog timer, and other critical configuration bits are set correctly for your application and hardware. Incorrect oscillator settings are a common cause of timing issues.

    2.  **Set Breakpoints to Isolate the Problem:**
        *   **Breakpoint 1 (Initialization):** Set a breakpoint at the very beginning of your `main()` function.
            *   **Purpose:** To confirm that the program is actually starting and reaching `main()`.
        *   **Breakpoint 2 (LED Pin Configuration):** Set a breakpoint immediately after the line(s) where you configure RA0 as an output (e.g., `TRISA0 = 0;` or `TRISA &= ~(1 << 0);`).
            *   **Purpose:** To verify that the pin direction register is correctly set.
        *   **Breakpoint 3 (LED Toggle Logic):** Set breakpoints inside your blinking loop, specifically on the lines where you toggle the LED state (e.g., `LATA0 = 1;` and `LATA0 = 0;`).
            *   **Purpose:** To see if the code is reaching these lines and attempting to change the LED state.
        *   **Breakpoint 4 (Delay Function):** Set a breakpoint at the beginning of your delay function (if you have one).
            *   **Purpose:** To check if the delay function is being called and if the program is getting stuck there.

    3.  **Start Debugging and Observe:**
        *   Click the "Debug Project" button in MPLAB X IDE.
        *   **Step 1:** When the program hits Breakpoint 1 (start of `main`), use the **Watch Window** (Window -> Debugging -> Watches) to add `TRISA` and `LATA` registers.
        *   **Step 2:** Use **Step Over** to advance to Breakpoint 2. Observe the `TRISA` register in the Watch Window. It should reflect that RA0 is configured as an output (e.g., the bit corresponding to RA0 should be 0). If not, there's an issue with your pin configuration code.
        *   **Step 3:** Use **Run** to continue execution. If the program hits Breakpoint 3 (LED ON line), observe `LATA` in the Watch Window. The bit for RA0 should change to 1. If the LED on the board doesn't turn ON, the issue is likely hardware (LED, resistor, connection) or the pin mapping.
        *   **Step 4:** Use **Step Over** to advance to the delay function call. If the program gets stuck in the delay function (e.g., an infinite loop within the delay), you'll see the program counter not advancing past the delay function's entry point. If it's a software delay, check the loop conditions. If it's a timer-based delay, check timer configurations.
        *   **Step 5:** Use **Run** again. If the program hits the LED OFF line (Breakpoint 3 again), observe `LATA`. The bit for RA0 should change to 0. If the LED on the board doesn't turn OFF, again, it points to hardware or pin mapping.

    4.  **Analyze and Refine:**
        *   **If the program never reaches `main()`:** Check configuration bits (especially oscillator and reset settings).
        *   **If `TRISA` isn't configured correctly:** Review your `TRISA` assignment.
        *   **If `LATA` bits change in the Watch Window but the LED doesn't respond:**
            *   **Hardware Issue:** Most likely a problem with the LED, resistor, wiring, or the physical pin on the PIC. Use a multimeter to check voltage on RA0.
            *   **Pin Mapping:** Ensure RA0 in your code corresponds to the physical pin you've connected the LED to.
        *   **If the program gets stuck in the delay or doesn't loop:** Use **Step Into** to go inside the delay function or the main loop to find where execution halts or deviates. Check loop conditions, variable increments/decrements, and timer configurations.
        *   **Use the Call Stack:** If you have multiple functions, the Call Stack can help you understand the flow if the program gets lost in a sub-function.

    By systematically using breakpoints, stepping commands, and the Watch Window, you can narrow down the problem from a general "LED not blinking" to a specific point of failure, whether it's in the code's logic, configuration, or the underlying hardware.