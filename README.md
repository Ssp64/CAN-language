# CAN Language

CAN is a small interpreted programming language implemented in Python. It
includes typed variables, arrays, functions, loops, input/output, built-in
utilities, and error handling.

## Requirements

- Python 3.8 or newer
- No third-party packages

## Getting Started

Run the included example:

```powershell
python canlang.py run hello.can
```

Start the interactive REPL:

```powershell
python canlang.py repl
```

Show the built-in reference:

```powershell
python canlang.py --help
```

## Hello World

Create a file named `example.can`:

```can
spill("Hello, CAN!");

think Ower name = "Aaren";
think etco age = 19;

spill("Name:", name);
spill("Age:", age);
```

Run it with:

```powershell
python canlang.py run example.can
```

Statements generally end with a semicolon.

## Types

| CAN type | Meaning | Example |
| --- | --- | --- |
| `yap` | Boolean | `fr`, `cap` |
| `etco` | Integer or floating-point number | `42`, `3.14` |
| `Ower` | String | `"hello"` |
| `nada` | Null value | `nada` |
| `rack` | Dynamic array | `[1, 2, 3]` |

Declare variables with `think`:

```can
think yap active = fr;
think etco score = 100;
think Ower message = "Ready";
think rack values = [10, 20, 30];

^ rack declarations may also omit "think"
rack names = ["Sam", "Aaren"];
```

## Output and Input

```can
spill("Printed with a newline");
spillRaw("Printed without a newline");

think Ower name = catch("Name: ");
think etco age = catchNum("Age: ");
```

## Conditions

```can
no cap (score > 50) {
    spill("High score");
}
lowkey (score == 50) {
    spill("Exactly fifty");
}
bet {
    spill("Low score");
}
```

## Loops

```can
think etco count = 3;

ghost (count > 0) {
    spill(count);
    count -= 1;
}

grind {
    count += 1;
} ghost (count < 3);

slide (i = 0; i < 5; i += 1) {
    spill(i);
}

rack colors = ["red", "green", "blue"];
foreach (color in colors) {
    spill(color);
}
```

Use `drop;` to break from a loop and `skip;` to continue to its next
iteration.

## Functions

Functions are declared with `vibe` and return values with `bounce`:

```can
vibe etco add(etco a, etco b) {
    bounce a + b;
}

vibe nada greet(Ower name) {
    spill("Hello", name);
}

spill(add(4, 6));
greet("CAN");
```

Variadic parameters use `*` and are received as a `rack`:

```can
vibe nada show(Ower* values) {
    foreach (value in values) {
        spill(value);
    }
}
```

## Arrays

```can
rack nums = [10, 20, 30];

spill(nums[0]);
nums[1] = 99;
nums.push(40);
spill(nums.pop());
```

Available array methods include:

```text
len, push, pop, shift, unshift, get, set, slice, contains,
indexOf, reverse, join, copy, clear, first, last, isEmpty, concat
```

Create a generated array with `newRack(size)` or
`newRack(size, fillValue)`.

## Strings

Available string methods include:

```text
len, upper, lower, trim, trimLeft, trimRight, reverse, contains,
startsWith, endsWith, indexOf, slice, replace, split, repeat,
charAt, toNum
```

Example:

```can
think Ower text = "  hello  ";
spill(text.trim().upper());
spill("CAN".repeat(3));
```

## Error Handling

Raise an error with `yeet` and catch it with `shield` and `miss`:

```can
shield {
    yeet "Something went wrong";
}
miss (error) {
    spill("Caught:", error);
}
```

Runtime failures from built-ins and methods can also be caught this way.

## Operators

```text
+  -  *  /  %  **          arithmetic
== != <  >  <= >=          comparison
&& || !                    logical
=  += -= *= /= %= **=      assignment
```

`&&` and `||` use short-circuit evaluation.

## Built-ins

### Conversion and Type Inspection

```text
len, toOwer, toEtco, toYap, typeOf
isYap, isEtco, isOwer, isNada, isRack
```

### Math

```text
floor, ceil, round, abs, max, min, pow, sqrt, log, sin, cos, tan
```

### Arrays, Strings, and Random Values

```text
newRack, range, chars, randInt, randNum
```

### Utility

```text
clock, exit
```

## Comments

```can
^ This is a single-line comment.

...
This is a multi-line comment.
...
```

## Project Files

- `canlang.py` contains the lexer, parser, runtime, interpreter, and CLI.
- `hello.can` is a basic example program.

