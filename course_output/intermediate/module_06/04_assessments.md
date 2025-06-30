# Module 6: Debugging and Development Workflow Assessment

## Section 1: Debugging Fundamentals (25 points)

1.  **Multiple Choice (5 points):** Which of the following error types is *most* likely to occur when your code runs but produces incorrect output, even though there are no syntax errors or crashes?
    a) Syntax Error
    b) Runtime Error
    c) Logical Error
    d) Indentation Error

    **Answer:** c) Logical Error

2.  **Short Answer (10 points):** Briefly explain the primary difference between using `print()` statements for debugging and using a dedicated debugger (like `pdb` in Python or an IDE's debugger). When might you prefer one over the other?

    **Answer:**
    `print()` statements are a simple, quick way to inspect variable values or confirm code execution flow at specific points. They require modifying the code and re-running the program for each change in inspection point.
    A dedicated debugger, on the other hand, provides a more powerful and dynamic environment. It allows you to:
    *   Pause execution at specific lines (breakpoints).
    *   Step through code line-by-line (`step`, `next`).
    *   Inspect and even modify variable values in real-time.
    *   Examine the call stack.
    *   Change the execution flow.
    You might prefer `print()` for very simple, quick checks or when a debugger is not readily available or too complex for the task. You would prefer a dedicated debugger for complex issues, deep dives into code execution, understanding call stacks, or when you need to dynamically explore code behavior without constantly editing and re-running your script.

3.  **Scenario/Code (10 points):** Consider the following Python function designed to calculate the factorial of a number. It contains a bug.

    ```python
    def calculate_factorial(n):
        if n == 0:
            return 1
        else:
            result = 0 # This line contains the bug
            for i in range(1, n + 1):
                result *= i
            return result

    print(calculate_factorial(5)) # Expected: 120, Actual: 0
    ```

    a) Identify the type of error present in the `calculate_factorial` function. (2 points)
    b) Describe how you would use `pdb` (Python Debugger) to find this specific bug. List the `pdb` commands you would use and what you would expect to see. (5 points)
    c) Provide the corrected code. (3 points)

    **Answer:**
    a) **Logical Error.** The code runs without crashing but produces an incorrect result (0 instead of 120 for `calculate_factorial(5)`).

    b) To use `pdb` to find this bug:
    1.  **Insert `pdb.set_trace()`:** Add `import pdb; pdb.set_trace()` right before the line `result = 0` or at the beginning of the `else` block.
        ```python
        def calculate_factorial(n):
            if n == 0:
                return 1
            else:
                import pdb; pdb.set_trace() # Debugger starts here
                result = 0
                for i in range(1, n + 1):
                    result *= i
                return result
        ```
    2.  **Run the script:** Execute the Python script. Execution will pause at the `pdb.set_trace()` call, and you'll see the `(Pdb)` prompt.
    3.  **Use `pdb` commands:**
        *   Type `n` (next) to execute the line `result = 0`.
        *   Type `p result` (print result) to inspect the value of `result`. You would see `0`.
        *   Type `n` again to enter the loop.
        *   Type `p i` to see the current value of `i` (which would be 1 in the first iteration).
        *   Type `n` to execute `result *= i`.
        *   Type `p result` again. You would still see `0` (because `0 * 1` is `0`). This immediately highlights that the initial value of `result` is causing the issue, as any number multiplied by 0 will remain 0.
    4.  **Quit `pdb`:** Once the bug is identified, type `q` to quit the debugger.

    c) **Corrected code:**
    ```python
    def calculate_factorial(n):
        if n == 0:
            return 1
        else:
            result = 1 # Corrected: Initialized to 1, as 1 is the multiplicative identity
            for i in range(1, n + 1):
                result *= i
            return result
    ```

## Section 2: Development Workflow (35 points)

1.  **Multiple Choice (5 points):** Which Git command is used to download changes from a remote repository to your local repository and automatically merge them?
    a) `git commit`
    b) `git push`
    c) `git pull`
    d) `git clone`

    **Answer:** c) `git pull`

2.  **Short Answer (5 points):** Explain the purpose of branching in Git. Why is it a crucial part of a collaborative development workflow?

    **Answer:**
    Branching in Git allows developers to diverge from the main line of development and work on new features, bug fixes, or experiments in isolation without affecting the stable codebase. It's crucial for collaboration because it enables multiple developers to work on different tasks simultaneously without interfering with each other's work. Each developer can create their own branch, make changes, test them, and then, once complete and stable, merge their changes back into the main branch. This prevents breaking the main codebase and facilitates parallel development.

3.  **Scenario (10 points):** You are working on a team project. Your colleague just finished implementing a new feature on their branch (`feature-x`) and wants to integrate it into the main development branch (`main`). Describe the typical Git commands and steps they would follow to achieve this, assuming they want to merge their feature branch into `main`.

    **Answer:**
    1.  **Ensure `feature-x` is up-to-date and committed:** The colleague should ensure all their changes on `feature-x` are committed.
    2.  **Switch to the `main` branch:**
        `git checkout main`
    3.  **Pull the latest changes from the remote `main` branch:** This ensures their local `main` branch is current before merging, preventing unnecessary conflicts.
        `git pull origin main`
    4.  **Merge `feature-x` into `main`:**
        `git merge feature-x`
    5.  **Resolve any merge conflicts:** If conflicts arise, they must be manually resolved, and the changes committed.
    6.  **Push the merged `main` branch to the remote repository:** This updates the shared `main` branch for the rest of the team.
        `git push origin main`
    7.  **(Optional but good practice):** Delete the `feature-x` branch locally and remotely after a successful merge, as it's no longer needed.
        `git branch -d feature-x` (local)
        `git push origin --delete feature-x` (remote)

4.  **Short Answer (10 points):** What is the primary difference between a "unit test" and an "integration test"? Provide a simple example for each.

    **Answer:**
    *   **Unit Test:** Focuses on testing individual, isolated components or functions of a software system to ensure they work correctly in isolation. Dependencies are often mocked or stubbed out.
        *   **Example:** Testing a Python function `calculate_tax(amount, rate)` to ensure it returns the correct tax amount for various inputs (e.g., `calculate_tax(100, 0.05)` returns `5.0`).
    *   **Integration Test:** Verifies that different modules, components, or services of a system interact and work together correctly as a group. It tests the interfaces and data flow between these components.
        *   **Example:** Testing a user registration flow where a web form submits data to a backend API, which then stores the user in a database. An integration test would verify that submitting the form successfully creates a new user record in the database and that the API responds correctly.

5.  **Short Answer (5 points):** Why is "code review" an important practice in a professional development environment? List at least two benefits.

    **Answer:**
    Code review is the systematic examination of computer source code by someone other than the author. It is important because:
    1.  **Improved Code Quality:** Helps identify bugs, logical errors, design flaws, and potential security vulnerabilities early in the development cycle, leading to more robust and reliable software.
    2.  **Knowledge Sharing and Learning:** Spreads knowledge about the codebase, design patterns, and best practices among team members, fostering collective code ownership and continuous learning.
    3.  **Consistency and Maintainability:** Ensures adherence to coding standards, improves code readability, and makes the codebase easier for others to understand, maintain, and extend in the future.
    4.  **Mentorship:** Provides an opportunity for more experienced developers to mentor junior developers by providing constructive feedback.

## Section 3: General Workflow Concepts (20 points)

1.  **Short Answer (5 points):** Briefly explain the concept of "Test-Driven Development" (TDD). What is the typical cycle?

    **Answer:**
    Test-Driven Development (TDD) is a software development process where tests are written *before* the actual code that implements the functionality. The core idea is to write a failing test, then write just enough code to make that test pass, and finally refactor the code while ensuring all tests still pass.
    The typical cycle is often described as **"Red-Green-Refactor"**:
    1.  **Red:** Write a small, failing test for a new piece of functionality (it fails because the code doesn't exist yet).
    2.  **Green:** Write *just enough* production code to make the failing test pass.
    3.  **Refactor:** Improve the code's design, readability, and efficiency without changing its external behavior (i.e., ensuring all tests continue to pass).

2.  **Short Answer (5 points):** Why is good documentation (e.g., API documentation, user manuals, internal comments) considered a crucial part of a robust development workflow?

    **Answer:**
    Good documentation is crucial because:
    1.  **Onboarding:** Helps new team members quickly understand the codebase, project architecture, and how different components interact.
    2.  **Maintenance and Debugging:** Makes it easier for developers (including their future selves) to understand, debug, and modify existing code, reducing the time spent reverse-engineering.
    3.  **Collaboration:** Facilitates clear communication and understanding among team members, especially for complex systems or when working asynchronously.
    4.  **Usability:** For external users or other developers consuming an API, clear and comprehensive documentation is essential for correct and efficient usage.
    5.  **Reduces Technical Debt:** Prevents knowledge silos and ensures that critical information about the system is preserved and accessible.

3.  **Short Answer (10 points):** In an Agile development context, what is a "sprint" and what is its primary goal?

    **Answer:**
    In an Agile development context (particularly in Scrum), a "sprint" is a fixed, short period of time (typically 1-4 weeks) during which a development team works to complete a set amount of work from the product backlog. It is a time-boxed iteration where a cross-functional team builds, tests, and delivers a potentially shippable increment of the product.

    The **primary goal** of a sprint is to deliver a valuable, working increment of software that meets the sprint goal, allowing for continuous feedback, inspection, and adaptation based on what was learned during the sprint. It aims to provide regular opportunities to deliver value and gather feedback from stakeholders.