// The cut. For a melee hit with an item, `source` is the item and its hierarchy parent the attacker (see
// PluginAdminLog.PlayerHitBy). On top of the blade's own damage each hit takes a share of the victim's full health:
// the share for the blade's state divided by N, N from SK_Settings for light or heavy (and sprint) attacks; the
// one that finishes it is a hit with SK_OneCut and the same
// source, so kill credit, the admin log and death animations all go the normal way.
class SK_Kill
{
	protected static bool s_Busy;

	static void OnHit(EntityAI victim, int damageType, EntityAI source, string ammo)
	{
		if (s_Busy || !victim || damageType != DamageType.CLOSE_COMBAT || !g_Game.IsServer())
			return;
		SK_Shashka blade = SK_Shashka.Cast(source);
		if (!blade || !victim.IsAlive())
			return;
		SK_Settings s = SK_Settings.Get();
		float share = s.DamageFor(blade.GetHealthLevel());
		if (share <= 0)
			return;

		int hits = s.HeavyHitsToKill;
		if (ammo == "SK_ShashkaLight")
			hits = s.LightHitsToKill;
		float cut = victim.GetMaxHealth("", "Health") * share / hits;

		s_Busy = true;
		if (victim.GetHealth("", "Health") <= cut + 0.001)
		{
			victim.ProcessDirectDamage(DamageType.CLOSE_COMBAT, blade, "", "SK_OneCut", "0 0 0", 1);
			if (victim.IsAlive())
				victim.SetHealth("", "", 0);	// in case a damage zone soaked the hit
		}
		else
		{
			victim.AddHealth("", "Health", -cut);
		}
		s_Busy = false;
	}

	static void OnKilled(Object killer)
	{
		if (!g_Game.IsServer())
			return;
		SK_Shashka blade = SK_Shashka.Cast(killer);
		if (blade)
			blade.SK_AddKill();
	}
}

modded class PlayerBase
{
	override void EEHitBy(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		super.EEHitBy(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
		SK_Kill.OnHit(this, damageType, source, ammo);
	}

	override void EEKilled(Object killer)
	{
		super.EEKilled(killer);
		SK_Kill.OnKilled(killer);
	}

	//! the bare blade on the back: melee and shoulder slots each per shashka.json
	override bool CanReceiveAttachment(EntityAI attachment, int slotId)
	{
		if (SK_Shashka.Cast(attachment))
		{
			string slot = InventorySlots.GetSlotName(slotId);
			slot.ToLower();
			if (slot == "melee" && !SK_Settings.Get().AllowMeleeSlot)
				return false;
			if (slot == "shoulder" && !SK_Settings.Get().AllowShoulderSlot)
				return false;
		}
		if (SK_Sheath.Cast(attachment))
		{
			string sheathSlot = InventorySlots.GetSlotName(slotId);
			sheathSlot.ToLower();
			if (sheathSlot == "shoulder" && !SK_Settings.Get().AllowSheathShoulder)
				return false;
		}
		return super.CanReceiveAttachment(attachment, slotId);
	}

	override void OnRPC(PlayerIdentity sender, int rpc_type, ParamsReadContext ctx)
	{
		if (rpc_type == SK_RPC_SETTINGS)
		{
			// settings only ever go server -> client: a client sending this to the server is ignored, or a
			// modified client could rewrite the server's numbers
			if (g_Game.IsDedicatedServer())
				return;
			if (!SK_Settings.Get().ReadFrom(ctx))
				Print("[Shashka] (E) bad settings from the server");
			return;
		}
		super.OnRPC(sender, rpc_type, ctx);
	}
}

modded class ZombieBase
{
	override void EEHitBy(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		super.EEHitBy(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
		SK_Kill.OnHit(this, damageType, source, ammo);
	}

	override void EEKilled(Object killer)
	{
		super.EEKilled(killer);
		SK_Kill.OnKilled(killer);
	}
}

modded class AnimalBase
{
	override void EEHitBy(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		super.EEHitBy(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
		SK_Kill.OnHit(this, damageType, source, ammo);
	}

	override void EEKilled(Object killer)
	{
		super.EEKilled(killer);
		SK_Kill.OnKilled(killer);
	}
}

// reach from the settings, on the attacker's client and on the server alike
modded class DayZPlayerImplementMeleeCombat
{
	override protected float GetWeaponRange(InventoryItem weapon, int weaponMode)
	{
		if (SK_Shashka.Cast(weapon))
			return SK_Settings.Get().Range(weaponMode);
		return super.GetWeaponRange(weapon, weaponMode);
	}
}

// the whetstone (recipe SharpenMelee -> PluginRepairing.Repair(player, whetstone, item))
modded class PluginRepairing
{
	//! vanilla lets a ruined item through here (an && / || precedence slip): a ruined shashka is gone for good
	override bool CanRepair(ItemBase repair_kit, Object item, string damage_zone = "")
	{
		if (SK_Shashka.Cast(item) && item.GetHealthLevel() == GameConstants.STATE_RUINED)
			return false;
		return super.CanRepair(repair_kit, item, damage_zone);
	}

	override bool Repair(PlayerBase player, ItemBase repair_kit, Object item, float specialty_weight, string damage_zone = "", bool use_kit_qty = true)
	{
		SK_Shashka blade = SK_Shashka.Cast(item);
		if (!blade)
			return super.Repair(player, repair_kit, item, specialty_weight, damage_zone, use_kit_qty);
		if (g_Game.IsServer())
			blade.SK_Sharpen(repair_kit, use_kit_qty);
		return true;
	}
}
