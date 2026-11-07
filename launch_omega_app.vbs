Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Start OMEGA + VISION server silently in background (0 = hidden window)
WshShell.Run "cmd /c cd /d """ & strPath & """ && python omega_server.py", 0, False

' Wait 2 seconds for server boot
WScript.Sleep 2000

' Launch OMEGA in clean standalone App mode (Edge or Chrome)
On Error Resume Next
WshShell.Run "msedge --app=http://localhost:8080", 1, False
If Err.Number <> 0 Then
    Err.Clear
    WshShell.Run "chrome --app=http://localhost:8080", 1, False
End If