#include <windows.h>
#include <urlmon.h>
#include <tlhelp32.h>
#include <iostream>
#include <string>
#include <filesystem>
#include <fstream>

#pragma comment(lib, "urlmon.lib")

// Check if process is running
bool IsProcessRunning(const std::wstring& processName) {
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) return false;

    PROCESSENTRY32W pe32 = { sizeof(PROCESSENTRY32W) };
    if (!Process32FirstW(hSnapshot, &pe32)) {
        CloseHandle(hSnapshot);
        return false;
    }

    bool found = false;
    do {
        if (_wcsicmp(pe32.szExeFile, processName.c_str()) == 0) {
            found = true;
            break;
        }
    } while (Process32NextW(hSnapshot, &pe32));

    CloseHandle(hSnapshot);
    return found;
}

// Terminate process by name
bool TerminateProcessByName(const std::wstring& processName) {
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) return false;

    PROCESSENTRY32W pe32 = { sizeof(PROCESSENTRY32W) };
    if (!Process32FirstW(hSnapshot, &pe32)) {
        CloseHandle(hSnapshot);
        return false;
    }

    bool terminated = false;
    do {
        if (_wcsicmp(pe32.szExeFile, processName.c_str()) == 0) {
            HANDLE hProcess = OpenProcess(PROCESS_TERMINATE, FALSE, pe32.th32ProcessID);
            if (hProcess) {
                if (TerminateProcess(hProcess, 0)) {
                    std::wcout << L"✅ Proces beëindigd (PID: " << pe32.th32ProcessID << L")\n";
                    terminated = true;
                }
                CloseHandle(hProcess);
            }
        }
    } while (Process32NextW(hSnapshot, &pe32));

    CloseHandle(hSnapshot);
    return terminated;
}

// Wait for process to close
bool WaitForProcessToClose(const std::wstring& processName, int maxSeconds = 45) {
    std::wcout << L"⏳ Wachten tot proces afgesloten is...\n";
    for (int i = 0; i < maxSeconds; ++i) {
        if (!IsProcessRunning(processName)) {
            std::wcout << L"✅ Proces afgesloten\n";
            return true;
        }
        Sleep(1000);
        if (i % 5 == 4) {
            std::wcout << L"   Nog " << (maxSeconds - i - 1) << L" seconden...\n";
        }
    }
    return false;
}

// Create batch script for delayed start
void CreateDelayedStartScript(const std::wstring& exePath) {
    std::wstring batchPath = exePath + L".starter.bat";
    std::wofstream bat(batchPath.c_str());
    bat << L"@echo off\n";
    bat << L"timeout /t 3 /nobreak >nul\n";
    bat << L"start \"\" \"" << exePath << L"\"\n";
    bat << L"del \"%~f0\"\n";  // Delete batch file itself
    bat.close();

    // Start batch file
    ShellExecuteW(NULL, L"open", batchPath.c_str(), NULL, NULL, SW_HIDE);
}

int wmain(int argc, wchar_t* argv[]) {
    SetConsoleOutputCP(CP_UTF8);

    if (argc < 3) {
        std::wcerr << L"Gebruik: updater.exe <download_url> <target_path>\n";
        return 1;
    }

    std::wstring url = argv[1];
    std::wstring targetPath = argv[2];
    std::wstring processName = std::filesystem::path(targetPath).filename().wstring();

    std::wcout << L"⛅ Weather Updater v1.25.1\n";
    std::wcout << L"============================\n\n";

    // Step 1: Wait for parent process to exit
    std::wcout << L"⏱️  Wachten 3 seconden voor parent process exit...\n";
    Sleep(3000);

    // Step 2: Check if process still running
    if (IsProcessRunning(processName)) {
        std::wcout << L"⚠️  " << processName << L" draait nog. Beëindigen...\n";
        TerminateProcessByName(processName);
        Sleep(2000);

        if (!WaitForProcessToClose(processName, 45)) {
            std::wcerr << L"❌ Kon proces niet afsluiten!\n";
            std::wcerr << L"   Sluit " << processName << L" handmatig en probeer opnieuw.\n";
            system("pause");
            return 1;
        }
    }

    // Step 3: Extra wait for DLL unload
    std::wcout << L"⏳ Extra wachttijd voor DLL cleanup...\n";
    Sleep(3000);

    // Step 4: Download new version
    wchar_t tempPath[MAX_PATH];
    wchar_t tempFile[MAX_PATH];
    GetTempPathW(MAX_PATH, tempPath);
    GetTempFileNameW(tempPath, L"aut", 0, tempFile);
    std::wstring tempDownload = tempFile;

    std::wcout << L"\n🔽 Downloaden...\n";
    HRESULT hr = URLDownloadToFileW(NULL, url.c_str(), tempDownload.c_str(), 0, NULL);
    if (FAILED(hr)) {
        std::wcerr << L"❌ Download mislukt! (0x" << std::hex << hr << L")\n";
        DeleteFileW(tempDownload.c_str());
        system("pause");
        return 1;
    }
    std::wcout << L"✅ Download voltooid\n";

    // Step 5: Backup old version
    std::wstring backupPath = targetPath + L".backup";
    if (std::filesystem::exists(targetPath)) {
        std::wcout << L"\n💾 Backup maken...\n";
        DeleteFileW(backupPath.c_str());

        // Try multiple times to delete/move old file
        bool deleted = false;
        for (int attempt = 0; attempt < 5; ++attempt) {
            SetFileAttributesW(targetPath.c_str(), FILE_ATTRIBUTE_NORMAL);
            
            if (MoveFileW(targetPath.c_str(), backupPath.c_str())) {
                std::wcout << L"✅ Backup gemaakt\n";
                deleted = true;
                break;
            }
            
            if (DeleteFileW(targetPath.c_str())) {
                std::wcout << L"✅ Oud bestand verwijderd\n";
                deleted = true;
                break;
            }

            std::wcout << L"   Poging " << (attempt + 1) << L"/5...\n";
            Sleep(2000);
        }

        if (!deleted) {
            std::wcerr << L"❌ Kan oud bestand niet verwijderen!\n";
            DeleteFileW(tempDownload.c_str());
            system("pause");
            return 1;
        }
    }

    // Step 6: Move new file
    std::wcout << L"\n📦 Installeren...\n";
    Sleep(1000);  // Extra wait

    bool moved = false;
    for (int attempt = 0; attempt < 5; ++attempt) {
        if (MoveFileW(tempDownload.c_str(), targetPath.c_str())) {
            std::wcout << L"✅ Nieuwe versie geïnstalleerd!\n";
            moved = true;
            break;
        }
        std::wcout << L"   Poging " << (attempt + 1) << L"/5...\n";
        Sleep(1500);
    }

    if (!moved) {
        std::wcerr << L"❌ Installatie mislukt!\n";
        // Restore backup
        if (std::filesystem::exists(backupPath)) {
            MoveFileW(backupPath.c_str(), targetPath.c_str());
        }
        DeleteFileW(tempDownload.c_str());
        system("pause");
        return 1;
    }

    // Step 7: Cleanup backup
    if (std::filesystem::exists(backupPath)) {
        DeleteFileW(backupPath.c_str());
    }

    // Step 8: Start new version via batch script (delayed)
    std::wcout << L"\n🚀 Starten van nieuwe versie...\n";
    CreateDelayedStartScript(targetPath);

    std::wcout << L"\n✅ Update succesvol!\n";
    std::wcout << L"   Venster sluit over 2 seconden...\n";
    Sleep(2000);

    return 0;
}
