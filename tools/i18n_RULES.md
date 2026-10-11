# Husk 简体中文本地化 —— 代码改造规则（务必严格遵守）

目标：让 Husk（SwiftUI iOS app）界面支持简体中文（zh-Hans），**且不破坏编译**。
本机**没有 Swift/Xcode，无法编译验证**，所以每条改动都必须类型正确、括号引号配平。

## 0. 黄金范例
先完整阅读 `src/app/Husk/OnboardingView.swift`（主控已按本规则改好），对照其写法。

## 1. 背景原理（重要）
下列 SwiftUI API 的**第一个字符串参数**在接收「字符串字面量」时，类型是
`LocalizedStringKey`，会**自动**从 Localizable 字符串表查找翻译，**不要改动**这类：
`Text`、`Button`、`Label`、`TextField`、`SecureField`、`Toggle`、`Picker`、`Section`、
`Menu`、`navigationTitle`、`alert`、`confirmationDialog`、`LabeledContent`、`GroupBox`、
`ProgressView`、`Stepper`、`navigationSubtitle`。

但当参数是 **String 变量 / 属性 / 三元运算 / 用 `+` 拼接的字符串**时，编译器选择
`Text(_ content: String)` 等 String 重载，**不会本地化**，必须按下面规则改造。

## 2. 改造规则

**R1 纯字面量拼接 → 合并为单个字面量。**
仅由字符串字面量和 `+` 组成（无变量、无 `\()` 插值）时，合并成一个完整字符串字面量，
注意连接处空格，使其重新成为 `LocalizedStringKey`。
```swift
// 前
Text("Boots the guest as soon as Husk opens, once JIT is "
   + "available. Off means you start it yourself.")
// 后
Text("Boots the guest as soon as Husk opens, once JIT is available. Off means you start it yourself.")
```

**R2 String 变量 / 属性 / 三元 / 函数返回值 → 显示处包 `LocalizedStringKey(_:)`。**
`LocalizedStringKey` 有初始化器 `init(_ value: String)`，会用该 String 内容做本地化 key，
查不到时原样显示（安全回退）。
```swift
Text(title)                                   -> Text(LocalizedStringKey(title))
Text(item.detail)                            -> Text(LocalizedStringKey(item.detail))
Label(state, systemImage: "x")               -> Label(LocalizedStringKey(state), systemImage: "x")
Button(cond ? "A" : "B") { ... }             -> Button(LocalizedStringKey(cond ? "A" : "B")) { ... }
TextField("Placeholder", text: $t)           // 字面量本就自动，勿动
// alert / confirmationDialog 标题为 String 变量时，传 LocalizedStringKey(...)；其 message 内的 Text 同理
```
**例外（不要包 LocalizedStringKey）**：内容是纯数字、百分比、字节大小、fps、时间/日期、
路径、游戏名/应用名/文件名（如 `app.label`、`live.label`、`name`、`title` 但其实是游戏名时）、
以及任何非英文自然语言句子。判断标准：值是「英文句子/单词组成的界面文案」才包；
是「数值/符号/专有名称」则不包。拿不准时，英文句子包，数字与名称不包。

**R3 自定义可复用视图 / 组件（重点：Theme.swift）。**
对承载文案的 `String` 形参（如 `title`、`text`、`message`、`subtitle`、`value`、`actionTitle`、
`detail`、`label`），**优先在该组件内部** `Text(...)` / `Label(...)` / `Button(...)` 显示点
包 `LocalizedStringKey(...)`，这样所有调用处无需改动即被覆盖。
若同一形参还参与非显示逻辑（拼接、比较、URL、写入），保持其类型为 String，仅在传给
SwiftUI 的那一点包。若组件形参只用于显示，也可直接把形参类型改为 `LocalizedStringKey`。

**R4 含运行时插值 `\(x)` 的 String 上下文。**
- 若本就是单个字面量直接传给 `Text/Label/...`（如 `Text("Starting \(name)…")`），
  它已是 `LocalizedStringKey` 插值，**不要改**。
- 若它处于 String 上下文（被拼接、赋给 String 变量/属性、在三元里、或为 String 形参），
  改用 `String(localized: "Template \(arg)")`（iOS 15+ 可用），保留插值变量与顺序。

**R5 绝对不要本地化 / 不要改动：**
- 日志与诊断：`HuskLog.log`、`os_log`、`Logger`、`NSLog`、`print`、
  `assertionFailure/precondition/fatalError`、`#function` 等的文本；
  `CrashReport.swift` 与 `AppDiagnosis.swift` 中**生成分享报告正文**的部分（报告保持英文）；
  QEMU/guest 启动的技术 log 行。注意：若某句「阶段标题/状态短语」是经 SwiftUI `Text`
  显示给用户看的（而非写进日志），则仍需本地化——按 R2 判断其显示点。
- URL、文件路径、SF Symbol 名（`Image(systemName:)`）、UserDefaults key、Notification 名、
  printf/日期格式串（如 `"%@"`、`"'Today,' h:mm a"`、`"%.0f fps"`）、JavaScript、Metal 着色器、
  shell 命令、Bundle/InfoDictionary key、bundle id、正则、NSPredicate、HTTP 头/JSON 字段名。
- 品牌与专有名词在译文中也保持原文：Husk、Android、TrollStore、StikDebug、StikJIT、Geode、
  Geometry Dash、Google、Google Play、Aurora、F-Droid、QEMU、Metal、ANGLE、MoltenVK、
  Unreal Engine、Unity、Godot、cocos2d、SDL、LÖVE、Minecraft、GTA、LineageOS、SideStore、AltStore。

**R6 最小改动原则。** 只做本地化必需修改；不重构、不改逻辑、不改缩进/空行风格；
不改变字符串含义；合并拼接时保留全部文字、标点与空格。不新增任何文件（除 R7 的 JSON）。

## 3. 每个文件改完后：登记 key（R7）
在 `tools/i18n_keys/` 目录下新建一个 JSON 文件，文件名把该 Swift 文件的相对路径中的
`/` 换成 `__`，再加 `.json`，例如 `src/app/Husk/Theme.swift` →
`tools/i18n_keys/Husk__Theme.swift.json`；
`src/app/HuskDownloadsWidget/DownloadsWidget.swift` →
`tools/i18n_keys/HuskDownloadsWidget__DownloadsWidget.swift.json`。
内容为该文件中**最终会作为本地化 key 的英文 UI 文案**去重数组（JSON 字符串数组）：
- 所有单个字面量 UI 文案；
- R1 合并后的完整句子；
- R2/R3 中被 `LocalizedStringKey(...)` 包裹的 String，其数据源处的英文字面量
  （例如枚举 `var title: String { ... return "English" }` 里 return 的英文句、静态常量）；
- R4 的 `String(localized:)` 模板，**用 `\(arg)` 形式保留占位**（例如 `"Starting \("name")…"` 写作
  `"Starting \(name)…"`，即普通插值写法）。
**不要**收录：数字、百分比、字节、日期、URL、路径、符号名、日志、报告正文、格式串、品牌名单独成词者。
JSON 必须合法（UTF-8、双引号、换行用 `\n`）。只登记英文，不需要翻译。

## 4. 不要触碰
- `src/app/Husk/OnboardingView.swift`（已完成，仅可阅读参考）。
- `project.yml`、所有 `Info.plist`、任何 `.xcstrings`、`.github/`、打包脚本
  （这些由主控统一处理）。不要新建 `.xcstrings` 或 `.lproj`。

## 5. 完成前自检
- 用 grep 复查该文件：UI 显示处是否还有「英文句子」以 String 拼接/变量形式漏网。
- 人工核对每处改动：括号、引号、`LocalizedStringKey(` 与 `)` 配平；三元两个分支类型一致；
  仅改了文案显示，不影响其它逻辑。
- 确认 `tools/i18n_keys/<name>.json` 合法且覆盖该文件全部 UI 文案。
