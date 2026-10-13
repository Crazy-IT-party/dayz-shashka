modded class MissionServer
{
	override void OnInit()
	{
		super.OnInit();
		SK_Settings.Get();				// load (or write) shashka.json at start, not on the first hit
		SK_Spawner.Start();
	}

	override void InvokeOnConnect(PlayerBase player, PlayerIdentity identity)
	{
		super.InvokeOnConnect(player, identity);
		SK_Settings.Get().SendTo(player, identity);
	}
}
