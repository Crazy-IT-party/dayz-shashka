// Gameplay numbers, from shashka.json in the server's @Shashka folder (shipped next to addons/), else from
// $profile:Shashka/shashka.json - written there with these defaults when neither exists, since scripts can't
// write into the mod folder. The server sends
// them to every client on connect: the melee range is worked out on the attacker's client as well.
const int SK_RPC_SETTINGS = 0x53484B31;	// "SHK1"

class SK_Settings
{
	int KillsToDamaged = 10;			// N: kills before the blade is damaged
	float BadlyDamagedFactor = 1.7;		// badly damaged after N * this kills
	float RuinedFactor = 3.0;			// ruined after N * this kills
	float WhetstoneCostPercent = 25;	// whetstone used up by one sharpening, % of a full stone
	int LightHitsToKill = 1;			// light attacks that kill anything (at a damage share of 1.0)
	int HeavyHitsToKill = 1;			// heavy (and sprint) attacks that kill anything
	// share of the target's full health one cut takes, by the blade's state (divided by the hits above);
	// 1.0 = one cut kills, 0 = only the Machete's own damage
	float DamagePristine = 1.0;
	float DamageWorn = 1.0;
	float DamageDamaged = 1.0;
	float DamageBadlyDamaged = 1.0;
	float DamageRuined = 0.0;
	float RangeLight = 1.9;				// reach, metres (the Machete's is 1.4)
	float RangeHeavy = 1.9;
	float RangeSprint = 3.8;			// the Machete's is 3.3
	bool AllowBelt = true;				// the sheath (with the blade in it) goes on a belt's left side
	bool AllowMeleeSlot = false;		// the bare blade on the back, melee slot
	bool AllowShoulderSlot = false;		// the bare blade on the back, shoulder slot
	bool AllowBackpackSlot = false;		// the bare blade on a backpack's strap (the Machete's place)
	bool AllowSheathShoulder = true;	// the sheath (with the blade in it) on the back, shoulder slot
	bool AllowSheathBackpack = true;	// the sheath (with the blade in it) on a backpack's strap
	bool SpawnUnderPaintings = true;	// sheaths with the blade in them under the soldiers' painting (SK_Spawner.c)
	int SpawnCount = 4;					// how many of those spots hold a sheath at a time
	int SpawnCheckMinutes = 30;			// how often the server tops them up

	protected static ref SK_Settings s_Instance;
	static string s_LoadedFrom;

	static SK_Settings Get()
	{
		if (!s_Instance)
		{
			if (g_Game.IsDedicatedServer())
				s_Instance = LoadServer();
			else
				s_Instance = new SK_Settings();	// the server's arrive by RPC
		}
		return s_Instance;
	}

	protected static SK_Settings LoadServer()
	{
		array<string> paths = {"$CurrentDir:@Shashka/shashka.json", "$profile:Shashka/shashka.json"};
		string error;
		SK_Settings s;
		foreach (string path : paths)
		{
			if (!FileExist(path))
				continue;
			if (JsonFileLoader<SK_Settings>.LoadFile(path, s, error) && s)
			{
				s_LoadedFrom = path;
				s.Sanitize();
				Print("[Shashka] settings from " + path + ": " + s.Describe());
				return s;
			}
			Print("[Shashka] (E) bad " + path + ": " + error + " - using defaults");
			return new SK_Settings();
		}
		s = new SK_Settings();
		MakeDirectory("$profile:Shashka");
		if (JsonFileLoader<SK_Settings>.SaveFile(paths[1], s, error))
		{
			s_LoadedFrom = paths[1];
			Print("[Shashka] no shashka.json in @Shashka - wrote defaults to " + paths[1] + ": " + s.Describe());
		}
		else
			Print("[Shashka] (E) no shashka.json and could not write " + paths[1] + ": " + error);
		return s;
	}

	void Sanitize()
	{
		if (KillsToDamaged < 1)		KillsToDamaged = 1;
		BadlyDamagedFactor = Math.Max(BadlyDamagedFactor, 1.0);
		RuinedFactor = Math.Max(RuinedFactor, BadlyDamagedFactor);
		WhetstoneCostPercent = Math.Clamp(WhetstoneCostPercent, 0, 100);
		if (LightHitsToKill < 1)	LightHitsToKill = 1;
		if (HeavyHitsToKill < 1)	HeavyHitsToKill = 1;
		DamagePristine = Math.Max(DamagePristine, 0);
		DamageWorn = Math.Max(DamageWorn, 0);
		DamageDamaged = Math.Max(DamageDamaged, 0);
		DamageBadlyDamaged = Math.Max(DamageBadlyDamaged, 0);
		DamageRuined = Math.Max(DamageRuined, 0);
		RangeLight = Math.Clamp(RangeLight, 0.5, 10);
		RangeHeavy = Math.Clamp(RangeHeavy, 0.5, 10);
		RangeSprint = Math.Clamp(RangeSprint, 0.5, 10);
		if (SpawnCount < 0)			SpawnCount = 0;
		if (SpawnCheckMinutes < 1)	SpawnCheckMinutes = 1;
	}

	string Describe()
	{
		string d = DescribeWear() + string.Format(", slots belt %1 melee %2 shoulder %3 backpack %4, sheath shoulder %5 backpack %6, spawns %7 x%8 every %9 min", AllowBelt, AllowMeleeSlot, AllowShoulderSlot, AllowBackpackSlot, AllowSheathShoulder, AllowSheathBackpack, SpawnUnderPaintings, SpawnCount, SpawnCheckMinutes);
		return d + string.Format(", damage pristine %1 worn %2 damaged %3 badly %4 ruined %5", DamagePristine, DamageWorn, DamageDamaged, DamageBadlyDamaged, DamageRuined);
	}

	protected string DescribeWear()
	{
		return string.Format("damaged@%1 badly@%2 ruined@%3 kills, whetstone %4 percent, hits light %5 heavy %6, range %7/%8/%9",
			KillsAt(GameConstants.STATE_DAMAGED), KillsAt(GameConstants.STATE_BADLY_DAMAGED), KillsAt(GameConstants.STATE_RUINED),
			WhetstoneCostPercent, LightHitsToKill, HeavyHitsToKill, RangeLight, RangeHeavy, RangeSprint);
	}

	//! kills at which the blade reaches a health level
	int KillsAt(int level)
	{
		switch (level)
		{
			case GameConstants.STATE_DAMAGED:		return KillsToDamaged;
			case GameConstants.STATE_BADLY_DAMAGED:	return Math.Ceil(KillsToDamaged * BadlyDamagedFactor);
			case GameConstants.STATE_RUINED:		return Math.Ceil(KillsToDamaged * RuinedFactor);
		}
		return 0;
	}

	//! the health level a blade with this many kills has
	int LevelForKills(int kills)
	{
		if (kills >= KillsAt(GameConstants.STATE_RUINED))			return GameConstants.STATE_RUINED;
		if (kills >= KillsAt(GameConstants.STATE_BADLY_DAMAGED))	return GameConstants.STATE_BADLY_DAMAGED;
		if (kills >= KillsAt(GameConstants.STATE_DAMAGED))			return GameConstants.STATE_DAMAGED;
		return GameConstants.STATE_PRISTINE;
	}

	//! share of full health one cut takes for a blade in this health level
	float DamageFor(int level)
	{
		switch (level)
		{
			case GameConstants.STATE_PRISTINE:		return DamagePristine;
			case GameConstants.STATE_WORN:			return DamageWorn;
			case GameConstants.STATE_DAMAGED:		return DamageDamaged;
			case GameConstants.STATE_BADLY_DAMAGED:	return DamageBadlyDamaged;
		}
		return DamageRuined;
	}

	//! weapon mode as the melee code numbers them: the order of MeleeModes in config.cpp
	float Range(int mode)
	{
		if (mode == 1)	return RangeHeavy;
		if (mode == 2)	return RangeSprint;
		return RangeLight;
	}

	// ---- client sync -------------------------------------------------------------------------------------------
	void SendTo(PlayerBase player, PlayerIdentity identity)
	{
		ScriptRPC rpc = new ScriptRPC();
		rpc.Write(KillsToDamaged);
		rpc.Write(BadlyDamagedFactor);
		rpc.Write(RuinedFactor);
		rpc.Write(WhetstoneCostPercent);
		rpc.Write(LightHitsToKill);
		rpc.Write(HeavyHitsToKill);
		rpc.Write(RangeLight);
		rpc.Write(RangeHeavy);
		rpc.Write(RangeSprint);
		rpc.Write(AllowBelt);
		rpc.Write(AllowMeleeSlot);
		rpc.Write(AllowShoulderSlot);
		rpc.Write(AllowBackpackSlot);
		rpc.Write(AllowSheathShoulder);
		rpc.Write(AllowSheathBackpack);
		rpc.Send(player, SK_RPC_SETTINGS, true, identity);
	}

	bool ReadFrom(ParamsReadContext ctx)
	{
		if (!ctx.Read(KillsToDamaged) || !ctx.Read(BadlyDamagedFactor) || !ctx.Read(RuinedFactor))
			return false;
		if (!ctx.Read(WhetstoneCostPercent) || !ctx.Read(LightHitsToKill) || !ctx.Read(HeavyHitsToKill))
			return false;
		if (!ctx.Read(RangeLight) || !ctx.Read(RangeHeavy) || !ctx.Read(RangeSprint))
			return false;
		if (!ctx.Read(AllowBelt) || !ctx.Read(AllowMeleeSlot) || !ctx.Read(AllowShoulderSlot) || !ctx.Read(AllowBackpackSlot))
			return false;
		if (!ctx.Read(AllowSheathShoulder) || !ctx.Read(AllowSheathBackpack))
			return false;
		return true;
	}
}
