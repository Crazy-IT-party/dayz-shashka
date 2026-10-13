// ============================================================================
//  Shashka - a Cossack шашка that kills in one cut, wears out by kills and is
//  sharpened back on a whetstone; worn in its sheath on the belt's left side.
//
//  Client + server mod. The model, textures and damage materials are our own
//  (tools/build_model.py); the animations and hands are the Machete's (animClass
//  Knife, inherited). Gameplay numbers live in shashka.json in the server's
//  @Shashka folder (scripts/4_World/Shashka/SK_Settings.c), not here: the
//  ranges below are only the fallback until the server's settings arrive.
// ============================================================================

class CfgPatches
{
	class Shashka
	{
		units[] = {"SK_Shashka", "SK_Sheath"};
		weapons[] = {};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Scripts", "DZ_Weapons_Melee", "DZ_Weapons_Melee_Blade"};
	};
};

class CfgMods
{
	class Shashka
	{
		dir = "Shashka";
		name = "Shashka";
		author = "Crazy IT-party";
		version = "1.0.3";
		type = "mod";
		dependencies[] = {"World", "Mission"};
		class defs
		{
			class worldScriptModule
			{
				value = "";
				files[] = {"Shashka/scripts/4_World"};
			};
			class missionScriptModule
			{
				value = "";
				files[] = {"Shashka/scripts/5_Mission"};
			};
		};
	};
};

// the sheath's slot for the blade
class CfgSlots
{
	class Slot_SK_Shashka
	{
		name = "SK_Shashka";
		displayName = "$STR_SK_Shashka_Name";
		ghostIcon = "set:dayz_inventory image:melee";
	};
};

// the sheath model's proxy for the blade's slot: a sheathed shashka is drawn there
class CfgNonAIVehicles
{
	class ProxyAttachment;
	class Proxysk_shashka: ProxyAttachment
	{
		scope = 2;
		inventorySlot = "SK_Shashka";
		model = "\Shashka\data\proxy\sk_shashka.p3d";
	};
};

// The blade's own ammo per attack, so the script can tell a light cut from a heavy one by name. Damage as the
// Machete's; the script adds the rest (SK_Kill.c).
class CfgAmmo
{
	class MeleeDamage;
	class MeleeSharpLight_3;
	class MeleeSharpHeavy_3;
	class SK_ShashkaLight: MeleeSharpLight_3 {};
	class SK_ShashkaHeavy: MeleeSharpHeavy_3 {};
	class SK_ShashkaSprint: MeleeSharpHeavy_3 {};
	// the finishing blow the script lands with the blade as source, so the kill is credited and logged as melee
	class SK_OneCut: MeleeDamage
	{
		class DamageApplied
		{
			type = "Melee";
			class Health { damage = 100000; };
			class Blood  { damage = 100000; };
			class Shock  { damage = 0; };
		};
	};
};

class CfgVehicles
{
	class Machete;
	class SK_Shashka: Machete
	{
		scope = 2;
		displayName = "$STR_SK_Shashka_Name";
		descriptionShort = "$STR_SK_Shashka_Desc";
		model = "\Shashka\data\shashka.p3d";
		weight = 850;
		itemSize[] = {1, 6};
		lootTag[] = {"Military", "Police"};
		lootCategory = "Weapons";
		// in its sheath, on the back (melee / shoulder) or on a backpack's strap - which of these a player may use
		// is up to shashka.json (SK_Shashka.c / SK_Kill.c check the slot)
		inventorySlot[] = {"SK_Shashka", "Melee", "Shoulder", "Backpack_1"};
		// the back and backpack slots' proxies would hang it blade up: turned over there, hilt up
		class InventorySlotsOffsets
		{
			class Melee      { position[] = {0, -0.05, 0}; orientation[] = {0, 0, 0}; };
			class Shoulder   { position[] = {0, -0.05, 0}; orientation[] = {0, 0, 0}; };
			class Backpack_1 { position[] = {0, 0.45, 0}; orientation[] = {0, 0, 180}; };
		};
		repairableWithKits[] = {4};        // whetstone
		repairCosts[] = {25};              // display only - the server takes shashka.json's whetstoneCostPercent
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 200;
					healthLevels[] =
					{
						{1.0, {"Shashka\data\shashka_blade.rvmat", "Shashka\data\shashka_hilt.rvmat"}},
						{0.7, {"Shashka\data\shashka_blade.rvmat", "Shashka\data\shashka_hilt.rvmat"}},
						{0.5, {"Shashka\data\shashka_blade_damage.rvmat", "Shashka\data\shashka_hilt_damage.rvmat"}},
						{0.3, {"Shashka\data\shashka_blade_badly.rvmat", "Shashka\data\shashka_hilt_badly.rvmat"}},
						{0.0, {"Shashka\data\shashka_blade_destruct.rvmat", "Shashka\data\shashka_hilt_destruct.rvmat"}}
					};
				};
			};
		};
		class MeleeModes
		{
			class Default { ammo = "SK_ShashkaLight";  range = 1.9; };
			class Heavy   { ammo = "SK_ShashkaHeavy";  range = 1.9; };
			class Sprint  { ammo = "SK_ShashkaSprint"; range = 3.8; };
		};
	};
	// the sheath: on the belt's left side (Belt_Left, where vanilla hangs the canteen), the blade in its own slot.
	// With the blade in, the model shows the hilt over the throat (selection "hilt", SK_Sheath.c).
	class Inventory_Base;
	class SK_Sheath: Inventory_Base
	{
		scope = 2;
		displayName = "$STR_SK_Sheath_Name";
		descriptionShort = "$STR_SK_Sheath_Desc";
		model = "\Shashka\data\shashka_sheath.p3d";
		weight = 450;
		itemSize[] = {1, 6};
		rotationFlags = 17;
		inventorySlot[] = {"Belt_Left", "Shoulder", "Backpack_1"};
		attachments[] = {"SK_Shashka"};
		// the model is hilt up with its origin where a hand holds it; on the belt it is shifted down so the throat
		// sits at the hip and the scabbard hangs, turned so the curve runs the other way; the shoulder slot's proxy
		// hangs things upside down, so there it is turned over, hilt at the shoulder; a backpack's strap slot takes it
		// as it takes the Hatchet, upright on the pack with its middle (between the bands) on the slot
		class InventorySlotsOffsets
		{
			class Belt_Left  { position[] = {0, -0.358, 0}; orientation[] = {0, 180, 0}; };
			class Shoulder   { position[] = {0, 0.50, 0}; orientation[] = {0, 0, 180}; };
			class Backpack_1 { position[] = {0, 0, 0}; orientation[] = {0, 0, 0}; };
		};
		lootTag[] = {"Village"};
		lootCategory = "Weapons";
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 150;
					healthLevels[] =
					{
						{1.0, {"Shashka\data\shashka_sheath.rvmat", "Shashka\data\shashka_hilt.rvmat"}},
						{0.7, {"Shashka\data\shashka_sheath.rvmat", "Shashka\data\shashka_hilt.rvmat"}},
						{0.5, {"Shashka\data\shashka_sheath_damage.rvmat", "Shashka\data\shashka_hilt_damage.rvmat"}},
						{0.3, {"Shashka\data\shashka_sheath_badly.rvmat", "Shashka\data\shashka_hilt_badly.rvmat"}},
						{0.0, {"Shashka\data\shashka_sheath_destruct.rvmat", "Shashka\data\shashka_hilt_destruct.rvmat"}}
					};
				};
			};
		};
	};
};
