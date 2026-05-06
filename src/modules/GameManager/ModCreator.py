from modules.FrontEnd.FrontEndMode import NxMode
from modules.logger import log, superlog
from modules.config import *
import re, os


class ResolutionVector:
    w: float | int = 16
    h: float | int = 9
    s: int = 1024

    def __init__(self, width, height):
        """Initialize the class with Width and Height of the desired Resolution."""

        self.w = float(width)
        self.h = float(height)

    def addShadows(self, shadows):
        """Add Shadow Resolution if game supports it."""

        self.s = float(shadows)

    def getShadowScale(self):
        """Get the amount of shadow increased in float."""

        return float(self.s / 1024)

    def getscale(self):
        """Get the Total Increase of resolution in float."""

        scale = float(self.w * self.h) / float(1920 * 1080)
        return scale

    def getFullScale(self):
        """Get the the higher scale between Resolution and Shadow Resolution."""

        if self.getShadowScale() > self.getscale():
            return self.getShadowScale()
        else:
            return self.getscale()

    def getRamLayout(self):
        """Get the Estimated Ram Layout."""

        layout = 0
        if self.getFullScale() < 0:
            layout = 0
        if self.getFullScale() > 1:
            layout = 1
        if self.getFullScale() > 5:
            layout = 2
        return layout


class ModCreator:

    @staticmethod
    def _parse_resolution_pair(raw) -> tuple[float, float]:
        """Parse UltraCam resolution Values like '1920x1080' or '{1280.00, 720.00}'."""
        s = str(raw).strip()
        if s.startswith("{") and s.endswith("}"):
            parts = [p.strip() for p in s.strip("{}").split(",")]
            return float(parts[0]), float(parts[1])
        if "x" in s.lower():
            a, b = s.lower().split("x", 1)
            return float(a), float(b)
        raise ValueError(f"Unrecognized resolution value: {raw!r}")

    @classmethod
    def CreateCheats(cls):
        """This function creates a cheat manager patcher, primarily used only for TOTK right now."""

        from modules.GameManager.CheatManager import Cheats

        Cheats.CreateCheats()

    @classmethod
    # This no longer works, it's currently disabled and unused, the logic may be refractored in the future.
    def CreateExefs(cls, patchinfo, directory, version_options, selected_options):
        """creates an EXEFs patch for the respective game."""

        for version_option in version_options:
            version = version_option.get("version", "")
            mod_path = os.path.join(directory, patchinfo.ModName, "exefs")

            # Create the directory if it doesn't exist
            os.makedirs(mod_path, exist_ok=True)

            filename = os.path.join(mod_path, f"{version}.pchtxt")
            all_values = []
            with open(filename, "w", encoding="utf-8") as file:
                file.write(version_option.get("Source", "") + "\n")
                file.write(version_option.get("nsobid", "") + "\n")
                file.write(version_option.get("offset", "") + "\n")

                for key, value in version_option.items():
                    if key not in ["Source", "nsobid", "offset", "version", "Version"] and not selected_options[key].get() == "Off":  # fmt: skip
                        pattern = r"@enabled\n([\da-fA-F\s]+)\n@stop"
                        matches = re.findall(pattern, value)
                        for match in matches:
                            hex_values = match.strip().split()
                            all_values.extend(hex_values)
                            # Print @enabled and then @stop at the end.

                file.write("@enabled\n")
                for i, value in enumerate(all_values):
                    file.write(value)
                    if i % 2 == 1 and i != len(all_values) - 1:
                        file.write("\n")
                    else:
                        file.write(" ")
                file.write("\n@stop\n")

    @classmethod
    def UCAutoPatcher(cls, Manager, Config, Name):
        """
        This function configues the mod's config file (.ini) dynamically based on games.
        Requires manager, which then fetches UserChoices from manager to read all the different parameters.

        Parameters:
        manager (FrontEnd): The frontend UI manager.
        config (configparser): The config file parser.
        """

        for i, (key, value) in enumerate(Manager.UltracamPatchJson.items()):
            if key != Name:
                continue

            patch_info = value

            for patch in Manager.UserChoices:
                if patch.lower() in ["resolution", "aspect", "aspect ratio"]:
                    continue

                try:
                    patch_dict = patch_info[patch]
                except Exception as e:
                    continue

                patch_class = patch_dict["Class"]
                patch_Config = patch_dict["Config_Class"]
                patch_Default = patch_dict["Default"]

                # Ensure we have the section required.
                if not Config.has_section(patch_Config[0]):
                    Config[patch_Config[0]] = {}

                # In case we have an auto patch.
                # fmt: off
                if Manager.UserChoices[patch] == "auto" or Manager.UserChoices[patch].get() == "auto":
                    if patch_class.lower() == "dropdown":
                        patch_Names = patch_dict["Values"]
                        Config[patch_Config[0]][patch_Config[1]] = str(patch_Names[patch_Default])
                    else:
                        Config[patch_Config[0]][patch_Config[1]] = str(patch_Default)
                    continue

                if patch_class.lower() == "bool" or patch_class.lower() == "scale":
                    Config[patch_Config[0]][patch_Config[1]] = Manager.UserChoices[patch].get()

                if patch_class.lower() == "dropdown":
                    # exclusive to dropdown.
                    patch_Names = patch_dict["Name_Values"]
                    patch_Values = patch_dict["Values"]
                    index = patch_Names.index(Manager.UserChoices[patch].get())
                    Config[patch_Config[0]][patch_Config[1]] = str(patch_Values[index])

    @classmethod
    def UCRyujinxRamPatcher(cls, manager, filemgr, layout):
        """Patches Ryujinx specific Settings, such as RAM from 4 or 8GB."""
        
        if not os.path.exists(filemgr._emuconfig):
            log.error(f"Ryujinx config doesn't exist {filemgr._emuconfig} Please Run Ryujinx or press Browse to direct the app to Ryujinx.exe")
            return

        if (read_ryujinx_version(filemgr._emuconfig) >= 54):
            # GreemDev Ryujinx
            write_ryujinx_config(filemgr, filemgr._emuconfig,  "dram_size", layout)
            log.warning(f"Expanding Ram Size to Type {layout}")
        else:
            # Original Ryujinx
            if layout > 0:
                log.warning(f"Expanding Ryujinx RAM mode to 8GB, {layout}")
                write_ryujinx_config(filemgr, filemgr._emuconfig,  "expand_ram", True)
            else:
                log.warning(f"Reverting Ryujinx RAM mode to 4GB, {layout}")
                write_ryujinx_config(filemgr, filemgr._emuconfig,  "expand_ram", False)

    @classmethod
    def UCLegacyRamPatcher(cls, Manager, FileMgr, Layout):
        """Patches bunch of settings in Legacy Emulators, VRAM, RAM etc. Based on Resolution and shadow resolution outputs mostly."""

        write_Legacy_config(Manager, FileMgr._gameconfig, Manager._patchInfo.ID, "Core", "memory_layout_mode", str(Layout))  # fmt: skip
        write_Legacy_config(Manager, FileMgr._gameconfig, Manager._patchInfo.ID, "System", "use_docked_mode", "true")  # fmt: skip

        if Layout > 0:
            write_Legacy_config(Manager, FileMgr._gameconfig, Manager._patchInfo.ID, "Renderer", "vram_usage_mode", "1")  # fmt: skip
        else:
            write_Legacy_config(Manager, FileMgr._gameconfig, Manager._patchInfo.ID, "Renderer", "vram_usage_mode", "0")  # fmt: skip

    @classmethod
    def UCResolutionPatcher(cls, FileMgr, Manager, Config, Name):
        """
        This function configues the mod's config file (.ini) dynamically based on games.
        This function requires the file manager in order to read the locations of Ryujinx config file and Legacy config file respectively.
        This function also uses the UI manager to read the state of our UI, if we are using "Legacy" or Ryujinx modes respectively.
        Requires manager, which then fetches UserChoices from manager to read the resolution, shadows and aspect ratios parameters.

        Parameters:
        filemgr (FileManager): the file manager is required here.
        manager (FrontEnd): The frontend UI manager.
        config (configparser): The config file parser.
        """

        for i, (key, value) in enumerate(Manager.UltracamPatchJson.items()):
            if key != Name:
                continue

            patch_info = value

            shadows = 1024
            if "shadows" in patch_info:
                try:
                    raw = Manager.UserChoices["shadows"].get()
                    if isinstance(raw, str) and raw.lower().startswith("x"):
                        shadows = int(raw[1:])
                    else:
                        shadows = int(str(raw).split("x")[0])
                except Exception:
                    shadows = 1024
            elif "shadow resolution" in Manager.UserChoices:
                try:
                    raw = Manager.UserChoices["shadow resolution"].get()
                    shadows = int(str(raw).split("x")[0])
                except Exception:
                    shadows = 1024

            res_block = None
            chosen = None

            if "resolution" in patch_info:
                res_block = patch_info["resolution"]
                try:
                    chosen = Manager.UserChoices["resolution"].get()
                except Exception:
                    chosen = res_block["Name_Values"][res_block["Default"]]
                raw_val = res_block["Values"][res_block["Name_Values"].index(chosen)]
                w, h = cls._parse_resolution_pair(raw_val)
            elif "docked" in patch_info:
                res_block = patch_info["docked"]
                try:
                    chosen = Manager.UserChoices["docked"].get()
                except Exception:
                    chosen = res_block["Name_Values"][res_block["Default"]]
                raw_val = res_block["Values"][res_block["Name_Values"].index(chosen)]
                w, h = cls._parse_resolution_pair(raw_val)
            else:
                log.warning(f"UCResolutionPatcher: no resolution/docked block for {Name}, skipping")
                return

            Resolution = ResolutionVector(w, h)
            Resolution.addShadows(shadows)

            if NxMode.isLegacy():
                # for emulator scale
                new_scale = 2
                if (Manager._patchInfo.ResolutionScale):
                    emuscale = int(Manager._EmulatorScale.get())
                    new_scale += emuscale - 1

                write_Legacy_config(Manager, FileMgr._gameconfig, Manager._patchInfo.ID, "Renderer", "resolution_setup", f"{new_scale}")  # fmt: skip
                cls.UCLegacyRamPatcher(Manager, FileMgr, Resolution.getRamLayout())

            if NxMode.isRyujinx():
                new_scale = 1
                if (Manager._patchInfo.ResolutionScale):
                    new_scale = int(Manager._EmulatorScale.get())

                write_ryujinx_config(FileMgr, FileMgr._emuconfig, "res_scale", new_scale)  # fmt: skip
                cls.UCRyujinxRamPatcher(Manager, FileMgr, Resolution.getRamLayout())

            legacy_res = patch_info.get("resolution")
            if legacy_res is not None and len(legacy_res.get("Config_Class", [])) >= 3:
                Section = legacy_res["Config_Class"][0]
                Width = legacy_res["Config_Class"][1]
                Height = legacy_res["Config_Class"][2]

                if not Config.has_section(Section):
                    Config[Section] = {}

                Config[Section][Width] = str(int(Resolution.w))
                Config[Section][Height] = str(int(Resolution.h))

    @classmethod
    def UCAspectRatioPatcher(cls, Manager, Config, Name):
        """
        Patches Aspect Ratios for specific games...

        Parameters:
        manager (Manager Class): The frontend UI manager.
        config (configparser): The config file parser.
        """

        for i, (key, value) in enumerate(Manager.UltracamPatchJson.items()):
            if key != Name:
                continue

            patch_info = value

            ar_key = None
            if "aspectratiov2" in patch_info and "aspectratiov2" in Manager.UserChoices:
                ar_key = "aspectratiov2"
            elif "aspect" in patch_info and "aspect" in Manager.UserChoices:
                ar_key = "aspect"

            if ar_key is None:
                return

            ar_block = patch_info[ar_key]
            if len(ar_block["Config_Class"]) < 3:
                # e.g. aspectratiov2 uses UCAutoPatcher (section + single key).
                return

            ARIndex = ar_block["Name_Values"].index(Manager.UserChoices[ar_key].get())
            AspectList_raw = ar_block["Values"][ARIndex]
            if isinstance(AspectList_raw, str):
                aw, ah = cls._parse_resolution_pair(AspectList_raw)
                AspectRatio = ResolutionVector(aw, ah)
            else:
                AspectRatio = ResolutionVector(AspectList_raw[0], AspectList_raw[1])

            Section = ar_block["Config_Class"][0]
            Width = ar_block["Config_Class"][1]
            Height = ar_block["Config_Class"][2]

            if not Config.has_section(Section):
                Config[Section] = {}

            Config[Section][Width] = str(AspectRatio.w)
            Config[Section][Height] = str(AspectRatio.h)
