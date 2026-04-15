#Requires AutoHotkey v2.0

target := A_ScriptDir "\..\..\..\1other\openclaw-front-secretary\tools\auto_work\prepare_vscode_desk.ahk"

if !FileExist(target) {
    MsgBox(
        "prepare_vscode_desk canonical not found.`n"
        . "expected: " target "`n"
        . "Run from C:\1other\openclaw-front-secretary or restore the extracted canonical first.",
        "1POW auto_work compatibility wrapper",
        "Iconx"
    )
    ExitApp(2)
}

Run('"' A_AhkPath '" "' target '"')
ExitApp(0)
