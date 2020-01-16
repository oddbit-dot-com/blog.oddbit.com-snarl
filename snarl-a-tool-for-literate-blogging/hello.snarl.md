## Printing text to the console

To print the phrase "Hello, world!" to the console, we can use the `printf`
function, like this:

```c="print hello"
printf("Hello, world!\n");
```

If we wrap this in a function, we get:

```c="main function"
int main(int argv, char **argc) {
  <<print hello>>

  return 0;
}
```

In order to avoid problems and compiler warnings, we really ought to include
the `stdio.h` header file before referring to the `printf` function:

```c="include header files"
#include <stdio.h>
```

```c=hello.c --file --hide
// This file was generated using snarl.

<<include header files>>

<<main function>>
```
