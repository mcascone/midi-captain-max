-- MIDI Captain Firmware Installer
-- Interactive macOS app that watches for device and installs firmware

use AppleScript version "2.4"
use scripting additions
use framework "Foundation"

-- Configuration
property firmwareSourcePath : "/usr/local/share/midicaptain-firmware"
property knownDeviceNames : {"CIRCUITPY", "MIDICAPTAIN"}
property pollInterval : 2 -- seconds between volume scans

-- State
property installerWindow : missing value
property selectedVolume : missing value

-- Main entry point
on run
	showInstallerWindow()
end run

-- Show the main installer window
on showInstallerWindow()
	set volumeList to getCircuitPyVolumes()
	
	if (count of volumeList) = 0 then
		-- No device found - show waiting dialog
		set userChoice to display dialog "No MIDI Captain device detected.

Connect your device via USB and wait for it to mount, or click 'Refresh' to scan again.

Looking for volumes named:
• CIRCUITPY
• MIDICAPTAIN
• Or any volume with boot_out.txt" buttons {"Quit", "Browse...", "Refresh"} default button "Refresh" with title "MIDI Captain Installer" with icon note
		
		if button returned of userChoice is "Refresh" then
			showInstallerWindow()
		else if button returned of userChoice is "Browse..." then
			browseForVolume()
		else
			tell me to quit
		end if
	else if (count of volumeList) = 1 then
		-- One device found - confirm and install
		set targetVolume to item 1 of volumeList
		confirmAndInstall({targetVolume})
	else
		-- Multiple devices found - let user choose one or more
		set chosenVolumes to choose from list volumeList with prompt "Multiple CircuitPython devices detected.

Select device(s) to install firmware:
(Hold Cmd to select multiple)" with title "MIDI Captain Installer" default items volumeList with multiple selections allowed
		
		if chosenVolumes is not false then
			confirmAndInstall(chosenVolumes)
		else
			-- User cancelled the list selection
			tell me to quit
		end if
	end if
end showInstallerWindow

-- Get list of volumes that look like CircuitPython devices
on getCircuitPyVolumes()
	set validVolumes to {}
	
	try
		-- Get all mounted volumes
		set allVolumes to paragraphs of (do shell script "ls /Volumes/")
		
		repeat with volName in allVolumes
			set volPath to "/Volumes/" & volName
			
			-- Check if it's a known device name
			if volName is in knownDeviceNames then
				set end of validVolumes to volName as string
			else
				-- Check for CircuitPython markers (boot_out.txt or code.py)
				try
					do shell script "test -f " & quoted form of (volPath & "/boot_out.txt") & " || test -f " & quoted form of (volPath & "/code.py")
					set end of validVolumes to volName as string
				end try
			end if
		end repeat
	end try
	
	return validVolumes
end getCircuitPyVolumes

-- Let user browse for a volume manually
on browseForVolume()
	try
		set chosenFolder to choose folder with prompt "Select your MIDI Captain device (CIRCUITPY volume):" default location (POSIX file "/Volumes/")
		set volPath to POSIX path of chosenFolder
		
		-- Extract volume name from path
		if volPath starts with "/Volumes/" then
			set volName to text 10 thru -2 of volPath -- Remove /Volumes/ prefix and trailing /
			-- Handle nested paths
			if volName contains "/" then
				set volName to text 1 thru ((offset of "/" in volName) - 1) of volName
			end if
			confirmAndInstall({volName})
		else
			display alert "Invalid Selection" message "Please select a volume under /Volumes/" as warning
			showInstallerWindow()
		end if
	on error
		showInstallerWindow()
	end try
end browseForVolume

-- Confirm installation and proceed (supports multiple volumes)
on confirmAndInstall(volumeNames)
	set deviceCount to count of volumeNames
	
	-- Verify all volumes still exist
	set validVolumes to {}
	
	repeat with volName in volumeNames
		set targetPath to "/Volumes/" & volName
		try
			do shell script "test -d " & quoted form of targetPath
			set end of validVolumes to volName as string
		end try
	end repeat
	
	if (count of validVolumes) = 0 then
		display alert "Devices Disconnected" message "None of the selected volumes are available." as warning
		showInstallerWindow()
		return
	end if
	
	-- Check if firmware source exists
	try
		do shell script "test -d " & quoted form of firmwareSourcePath
	on error
		display alert "Firmware Not Found" message "Firmware files not found at:
" & firmwareSourcePath & "

Please reinstall the MIDI Captain Firmware package." as critical
		return
	end try
	
	-- Build confirmation message
	if deviceCount = 1 then
		set targetPath to "/Volumes/" & (item 1 of validVolumes)
		set confirmMessage to "Install MIDI Captain firmware to:
" & targetPath
	else
		set confirmMessage to "Install MIDI Captain firmware to " & (count of validVolumes) & " devices:
"
		repeat with volName in validVolumes
			set confirmMessage to confirmMessage & "• /Volumes/" & volName & "
"
		end repeat
	end if
	
	set confirmMessage to confirmMessage & "
Files to install:
• code.py (main firmware)
• boot.py (startup config)
• config.json (if not already present)
• config-mini6.json (Mini6 defaults)
• core/ (firmware modules)
• devices/ (hardware definitions)
• fonts/ (display fonts)

The firmware auto-detects your device type."
	
	set userChoice to display dialog confirmMessage buttons {"Cancel", "Install"} default button "Install" with title "Confirm Installation" with icon note
	
	if button returned of userChoice is "Install" then
		performInstallation(validVolumes)
	else
		showInstallerWindow()
	end if
end confirmAndInstall

-- Perform the actual installation (supports multiple devices)
on performInstallation(volumeList)
	set successCount to 0
	set failedVolumes to {}
	set deviceCount to count of volumeList

	repeat with volumeName in volumeList
		set targetPath to "/Volumes/" & volumeName

		try
			-- Delegate to the CLI installer (single source of truth for copy
			-- ordering and verification). Installed by the .pkg to
			-- /usr/local/bin/midicaptain-install alongside the firmware files.
			set installResult to do shell script "/usr/local/bin/midicaptain-install " & quoted form of targetPath
			set successCount to successCount + 1
		on error errMsg
			set end of failedVolumes to volumeName
		end try
	end repeat
	
	-- Build result message
	if successCount = deviceCount then
		-- All succeeded
		if deviceCount = 1 then
			set successMessage to "✓ Firmware installed successfully!

The device will restart automatically.
If it doesn't, disconnect and reconnect USB."
		else
			set successMessage to "✓ Firmware installed to " & successCount & " devices!

Devices will restart automatically.
If they don't, disconnect and reconnect USB."
		end if
		
		display dialog successMessage buttons {"Done", "Install Another"} default button "Done" with title "Installation Complete" with icon note
		
		if button returned of result is "Install Another" then
			showInstallerWindow()
		else
			tell me to quit
		end if
	else if successCount > 0 then
		-- Partial success
		set partialMessage to "⚠️ Installed to " & successCount & " of " & deviceCount & " devices.

Failed:"
		repeat with failedVol in failedVolumes
			set partialMessage to partialMessage & "
• " & failedVol
		end repeat
		
		display alert "Partial Installation" message partialMessage as warning buttons {"Done", "Retry"} default button "Retry"
		if button returned of result is "Retry" then
			showInstallerWindow()
		else
			tell me to quit
		end if
	else
		-- All failed
		display alert "Installation Failed" message "Could not install to any selected device." as critical buttons {"Quit", "Try Again"} default button "Try Again"
		if button returned of result is "Try Again" then
			showInstallerWindow()
		else
			tell me to quit
		end if
	end if
end performInstallation
