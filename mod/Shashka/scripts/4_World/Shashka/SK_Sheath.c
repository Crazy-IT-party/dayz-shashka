// The sheath. Goes on the belt's left side, the back's shoulder slot or a backpack's strap (each as shashka.json
// allows; the shoulder slot is checked in PlayerBase.CanReceiveAttachment) and holds the blade in its own slot. The blade
// shows through the model's proxy for that slot (CfgNonAIVehicles Proxysk_shashka): hilt out of the throat, the rest
// inside the scabbard - so an empty sheath and a full one need no script.
class SK_Sheath extends Inventory_Base
{
	SK_Shashka SK_GetBlade()
	{
		return SK_Shashka.Cast(FindAttachmentBySlotName("SK_Shashka"));
	}

	override bool CanPutAsAttachment(EntityAI parent)
	{
		if (!super.CanPutAsAttachment(parent))
			return false;
		if (!parent.IsClothing())
			return true;
		// a belt has the Belt_Left slot
		if (parent.GetInventory().HasAttachmentSlot(InventorySlots.GetSlotIdFromString("Belt_Left")))
			return SK_Settings.Get().AllowBelt;
		// bags: the Backpack_1 slot sits differently in every bag model. On these backpacks it holds the sheath
		// upright on the pack, as the Hatchet; on the canvas, messenger and sling bags it lies at the hip, so not those
		array<string> bags = {"TaloonBag_ColorBase", "HuntingBag", "MountainBag_ColorBase",
			"AliceBag_ColorBase", "CoyoteBag_ColorBase", "AssaultBag_ColorBase", "Attack2Bag_ColorBase",
			"ChildBag_ColorBase", "DryBag_ColorBase", "DrysackBag_ColorBase", "ImprovisedBag", "FurImprovisedBag",
			"TortillaBag"};
		foreach (string bag : bags)
		{
			if (parent.IsKindOf(bag))
				return SK_Settings.Get().AllowSheathBackpack;
		}
		return false;
	}
}

// how a hand holds the sheath: closed round it, as round the Machete's handle (its grip IK), with the ordinary
// one-handed animations - carried, not wielded. Without this it gets the generic open-handed hold.
modded class ModItemRegisterCallbacks
{
	override void RegisterOneHanded(DayZPlayerType pType, DayzPlayerItemBehaviorCfg pBehavior)
	{
		super.RegisterOneHanded(pType, pBehavior);
		pType.AddItemInHandsProfileIK("SK_Sheath", "dz/anims/workspaces/player/player_main/player_main_1h.asi", pBehavior, "dz/anims/anm/player/ik/gear/machete.anm");
	}
}
