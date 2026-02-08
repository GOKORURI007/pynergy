### 格式字符 [¶](https://docs.python.org/3/library/struct.html#format-characters "链接到此标题")

格式字符具有以下含义；给定它们的类型，C 和 Python 值之间的转换应该是显而易见的。"标准大小"
列指的是使用标准大小时打包值的字节大小；也就是说，当格式字符串以 `'<'`、`'>'`、`'!'` 或 `'='`
之一开头时。使用本机大小时，打包值的大小取决于平台。

| 格式 | C 类型           | Python 类型  | 标准大小 | 注释       |
|----|----------------|------------|------|----------|
| x  | 填充字节           | 无值         |      | (7)      |
| c  | char           | 长度为 1 的字节串 | 1    |          |
| b  | 有符号字符          | 整数         | 1    | (1), (2) |
| B  | 无符号字符          | 整数         | 1    | (2)      |
| ?  | _Bool          | 布尔值        | 1    | (1)      |
| h  | short          | 整数         | 2    | (2)      |
| H  | 无符号 short      | 整数         | 2    | (2)      |
| i  | int            | 整数         | 4    | (2)      |
| I  | 无符号 int        | 整数         | 4    | (2)      |
| l  | long           | 整数         | 4    | (2)      |
| L  | 无符号 long       | 整数         | 4    | (2)      |
| q  | long long      | 整数         | 8    | (2)      |
| Q  | 无符号 long long  | 整数         | 8    | (2)      |
| n  | ssize_t        | 整数         |      | (3)      |
| N  | size_t         | 整数         |      | (3)      |
| e  | (6)            | 浮点数        | 2    | (4)      |
| f  | float          | 浮点数        | 4    | (4)      |
| d  | double         | 浮点数        | 8    | (4)      |
| F  | float complex  | 复数         | 8    | (10)     |
| D  | double complex | 复数         | 16   | (10)     |
| s  | char[]         | 字节串        |      | (9)      |
| p  | char[]         | 字节串        |      | (8)      |
| P  | void*          | 整数         |      | (5)      |

在版本 3.3 中更改：添加了对 `'n'` 和 `'N'` 格式的支持。

在版本 3.6 中更改：添加了对 `'e'` 格式的支持。

在版本 3.14 中更改：添加了对 `'F'` 和 `'D'` 格式的支持。

注释：

1. `'?'` 转换代码对应于 C99 标准定义的 _Bool 类型。在标准模式下，它由一个字节表示。

2. 当尝试使用任何整数转换代码打包非整数时，如果非整数具有 [
   `__index__()`](https://docs.python.org/3/reference/datamodel.html#object.__index__ "object.__index__")
   方法，则会调用该方法将参数转换为整数后再进行打包。

   在版本 3.2 中更改：添加了对非整数使用 [
   `__index__()`](https://docs.python.org/3/reference/datamodel.html#object.__index__ "object.__index__")
   方法的支持。

3. `'n'` 和 `'N'` 转换代码仅适用于本机大小（默认选择或使用 `'@'` 字节顺序字符）。对于标准大小，您可以使用适合您应用程序的其他整数格式。

4. 对于 `'f'`、`'d'` 和 `'e'` 转换代码，打包表示使用 IEEE 754 binary32、binary64 或 binary16 格式（分别对应
   `'f'`、`'d'` 或 `'e'`），无论平台使用的浮点格式如何。

5. `'P'` 格式字符仅适用于本机字节顺序（默认选择或使用 `'@'` 字节顺序字符）。字节顺序字符 `'='`
   根据主机系统选择使用小端或大端顺序。struct 模块不将其解释为本机顺序，因此 `'P'` 格式不可用。

6. IEEE 754 binary16"半精度"类型在 2008
   年修订的 [IEEE 754 标准](https://en.wikipedia.org/wiki/IEEE_754-2008_revision) 中引入。它有一个符号位、5
   位指数和 11 位精度（其中 10 位显式存储），可以在全精度下表示大约 `6.1e-05` 到 `6.5e+04` 之间的数字。这种类型不受
   C 编译器广泛支持：在典型机器上，unsigned short
   可用于存储，但不能用于数学运算。有关更多信息，请参见维基百科关于 [半精度浮点格式](https://en.wikipedia.org/wiki/Half-precision_floating-point_format)
   的页面。

7. 打包时，`'x'` 插入一个 NUL 字节。

8. `'p'` 格式字符编码"Pascal字符串"，即存储在 _fixed number of bytes_
   中的短变长字符串，由计数给出。存储的第一个字节是字符串的长度，或
   255，以较小者为准。字符串的字节跟随其后。如果传递给 [
   `pack()`](https://docs.python.org/3/library/struct.html#struct.pack "struct.pack") 的字符串太长（超过计数减
   1），则只存储字符串的前 `count-1` 个字节。如果字符串短于 `count-1`，则用空字节填充，使总共使用恰好
   count 个字节。请注意，对于 [
   `unpack()`](https://docs.python.org/3/library/struct.html#struct.unpack "struct.unpack")，`'p'`
   格式字符消耗 `count` 个字节，但返回的字符串永远不会包含超过 255 个字节。

9. 对于 `'s'` 格式字符，计数被解释为字节的长度，而不是像其他格式字符那样的重复计数；例如，`'10s'` 意味着单个
   10 字节字符串映射到或来自单个 Python 字节串，而 `'10c'` 意味着 10 个单独的单字节字符元素（例如，
   `cccccccccc`）映射到或来自十个不同的 Python
   字节对象。（请参见 [示例](https://docs.python.org/3/library/struct.html#struct-examples)
   了解差异的具体演示。）如果未给出计数，则默认为
   1。打包时，字符串会被截断或用空字节填充以使其合适。解包时，结果字节对象总是恰好具有指定数量的字节。作为一种特殊情况，
   `'0s'` 表示单个空字符串（而 `'0c'` 表示 0 个字符）。

10. 对于 `'F'` 和 `'D'` 格式字符，打包表示使用 IEEE 754 binary32 和 binary64
    格式来表示复数的组件，无论平台使用的浮点格式如何。请注意，复数类型（`F` 和 `D`）无条件可用，尽管复数类型是
    C 中的可选功能。正如 C11 标准所规定，每个复数类型由包含实部和虚部分别的两元素 C 数组表示。

格式字符前面可以加上整数重复计数。例如，格式字符串 `'4h'` 与 `'hhhh'` 完全相同。

格式之间的空白字符被忽略；但是计数和其格式之间不得包含空白字符。

当使用整数格式之一（`'b'`、`'B'`、`'h'`、`'H'`、`'i'`、`'I'`、`'l'`、`'L'`、`'q'`、`'Q'`）打包值 `x` 时，如果
`x` 超出该格式的有效范围，则会引发 [
`struct.error`](https://docs.python.org/3/library/struct.html#struct.error "struct.error")。

在版本 3.1 中更改：以前，某些整数格式会包装超出范围的值并引发 [
`DeprecationWarning`](https://docs.python.org/3/library/exceptions.html#DeprecationWarning "DeprecationWarning")
而不是 [
`struct.error`](https://docs.python.org/3/library/struct.html#struct.error "struct.error")。

对于 `'?'` 格式字符，返回值要么是 [
`True`](https://docs.python.org/3/library/constants.html#True "True") 要么是 [
`False`](https://docs.python.org/3/library/constants.html#False "False")。打包时，使用参数对象的真值。在本机或标准布尔表示中，0
或 1 将被打包，任何非零值在解包时将是 `True`。
