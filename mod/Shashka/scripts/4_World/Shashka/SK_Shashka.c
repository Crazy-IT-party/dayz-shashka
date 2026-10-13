// The blade. Behaves as the Machete (animations, finishers, actions) except for wear: a swing doesn't blunt it,
// kills do (SK_Settings: damaged / badly damaged / ruined after so many kills). The kill count is saved with the
// item. Sharpening on a whetstone takes it up one level and sets the count back to that level's start.
class SK_Shashka extends Machete
{
	protected int m_SK_Kills;

	int SK_GetKills()
	{
		return m_SK_Kills;
	}

	void SK_AddKill()
	{
		m_SK_Kills++;
		int level = SK_Settings.Get().LevelForKills(m_SK_Kills);
		if (level > GetHealthLevel())					// only ever wears it further: other damage stands
			SK_SetLevel(level);
	}

	//! set the kill count and the level that goes with it (for admin tools)
	void SK_SetKills(int kills)
	{
		m_SK_Kills = Math.Max(kills, 0);
		SK_SetLevel(SK_Settings.Get().LevelForKills(m_SK_Kills));
	}

	//! one sharpening: up a level (worn counts as pristine), the whetstone pays for it. False if nothing to do.
	bool SK_Sharpen(ItemBase whetstone, bool useQuantity)
	{
		int level = GetHealthLevel();
		if (level == GameConstants.STATE_PRISTINE || level == GameConstants.STATE_RUINED)
			return false;
		int target = level - 1;
		if (target == GameConstants.STATE_WORN)
			target = GameConstants.STATE_PRISTINE;
		SK_Settings s = SK_Settings.Get();
		m_SK_Kills = s.KillsAt(target);
		SK_SetLevel(target);
		if (whetstone && useQuantity && whetstone.HasQuantity())
		{
			float cost = s.WhetstoneCostPercent * whetstone.GetQuantityMax() / 100;
			whetstone.AddQuantity(-Math.Min(cost, whetstone.GetQuantity()));
		}
		return true;
	}

	protected void SK_SetLevel(int level)
	{
		SetHealth01("", "Health", GetHealthLevelValue(level));
	}

	//! where it may hang, per shashka.json: in its sheath always, on a backpack's strap if allowed (the back slots
	//! are the player's call, PlayerBase.CanReceiveAttachment in SK_Kill.c, since only the slot tells them apart)
	override bool CanPutAsAttachment(EntityAI parent)
	{
		if (!super.CanPutAsAttachment(parent))
			return false;
		if (SK_Sheath.Cast(parent) || PlayerBase.Cast(parent))
			return true;
		return SK_Settings.Get().AllowBackpackSlot;
	}

	//! no wear per swing: the kills wear it
	override EntityAI ProcessMeleeItemDamage(int mode = 0)
	{
		return this;
	}

	override void OnStoreSave(ParamsWriteContext ctx)
	{
		super.OnStoreSave(ctx);
		ctx.Write(m_SK_Kills);
	}

	override bool OnStoreLoad(ParamsReadContext ctx, int version)
	{
		if (!super.OnStoreLoad(ctx, version))
			return false;
		return ctx.Read(m_SK_Kills);
	}
}
