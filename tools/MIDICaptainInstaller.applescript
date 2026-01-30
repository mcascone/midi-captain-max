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
		end if
	else if (count of volumeList) = 1 then
		-- One device found - confirm and install
		set targetVolume to item 1 of volumeList
		confirmAndInstall(targetVolume)
	else
		-- Multiple devices found - let user choose
		set chosenVolume to choose from list volumeList with prompt "Multiple CircuitPython devices detected.

Select the device to install firmware:" with title "MIDI Captain Installer" default items {item 1 of volumeList}
		
		if chosenVolume is not false then
			confirmAndInstall(item 1 of chosenVolume)
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
			confirmAndInstall(volName)
		else
			display alert "Invalid Selection" message "Please select a volume under /Volumes/" as warning
			showInstallerWindow()
		end if
	on error
		showInstallerWindow()
	end try
end browseForVolume

-- Confirm installation and proceed
on confirmAndInstall(volumeName)
	set targetPath to "/Volumes/" & volumeName
	
	-- Verify the volume still exists
	try
		do shell script "test -d " & quoted form of targetPath
	on error
		display alert "Device Disconnected" message "The volume '" & volumeName & "' is no longer available." as warning
		showInstallerWindow()
		return
	end try
	
	-- Check if firmware source exists
	try
		do shell script "test -d " & quoted form of firmwareSourcePath
	on error
		display alert "Firmware Not Found" message "Firmware files not found at:
" & firmwareSourcePath & "

Please reinstall the MIDI Captain Firmware package." as critical
		return
	end try
	
	-- Check for existing config.json
	set hasExistingConfig to false
	try
		do shell script "test -f " & quoted form of (targetPath & "/config.json")
		set hasExistingConfig to true
	end try
	
	set confirmMessage to "Install MIDI Captain firmware to:
" & targetPath & "

Files to install:
• code.py (main firmware)
• boot.py (startup config)
• devices/ (hardware definitions)
• fonts/ (display fonts)"
	
	if hasExistingConfig then
		set confirmMessage to confirmMessage & "

⚠️ Existing config.json will be preserved."
	else
		set confirmMessage to confirmMessage & "
• config.json (default configuration)"
	end if
	
	set userChoice to display dialog confirmMessage buttons {"Cancel", "Install"} default button "Install" with title "Confirm Installation" with icon note
	
	if button returned of userChoice is "Install" then
		performInstallation(volumeName, hasExistingConfig)
	else
		showInstallerWindow()
	end if
end confirmAndInstall

-- Perform the actual installation
on performInstallation(volumeName, preserveConfig)
	set targetPath to "/Volumes/" & volumeName
	
	-- Show progress
	display notification "Installing firmware..." with title "MIDI Captain Installer"
	
	try
		-- Copy code.py
		do shell script "cp " & quoted form of (firmwareSourcePath & "/code.py") & " " & quoted form of (targetPath & "/code.py")
		
		-- Copy boot.py
		do shell script "cp " & quoted form of (firmwareSourcePath & "/boot.py") & " " & quoted form of (targetPath & "/boot.py")
		
		-- Copy config.json only if no existing config
		if not preserveConfig then
			do shell script "cp " & quoted form of (firmwareSourcePath & "/config.json") & " " & quoted form of (targetPath & "/config.json")
		end if
		
		-- Copy devices/ directory
		do shell script "rm -rf " & quoted form of (targetPath & "/devices") & " && cp -R " & quoted form of (firmwareSourcePath & "/devices") & " " & quoted form of (targetPath & "/devices")
		
		-- Copy fonts/ directory
		do shell script "rm -rf " & quoted form of (targetPath & "/fonts") & " && cp -R " & quoted form of (firmwareSourcePath & "/fonts") & " " & quoted form of (targetPath & "/fonts")
		
		-- Sync to ensure files are written
		do shell script "sync"
		
		-- Success!
		set successMessage to "✓ Firmware installed successfully!

The device will restart automatically.
If it doesn't, disconnect and reconnect USB."
		
		if preserveConfig then
			set successMessage to successMessage & "

Your existing config.json was preserved."
		end if
		
		display dialog successMessage buttons {"Done", "Install Another"} default button "Done" with title "Installation Complete" with icon note
		
		if button returned of result is "Install Another" then
			showInstallerWindow()
		end if
		
	on error errMsg
		display alert "Installation Failed" message "Error: " & errMsg as critical buttons {"Quit", "Try Again"} default button "Try Again"
		if button returned of result is "Try Again" then
			showInstallerWindow()
		end if
	end try
end performInstallation
