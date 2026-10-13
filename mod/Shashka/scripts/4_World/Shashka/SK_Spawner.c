// Sheaths (a shashka in each) under the painting of charging soldiers in village houses. The spots - every such
// painting on the map, world positions - come with the mission: $mission:shashka/spots.json, written by
// tools/spawns.py. Every SpawnCheckMinutes the server tops the spots up so that SpawnCount of them hold a sheath;
// one taken away frees its spot. The economy keeps their lifetime (shashka/types.xml, nominal 0). Server only.
// the sheath model's chape relative to its origin (the hand's place; tools/build_model.py sheath_grip)
const vector SK_SHEATH_CHAPE = "0.049 -0.552 0";

class SK_Spot
{
	vector Pos;		// on the floor under the painting
	vector Wall;	// the way to the wall
}

class SK_SpotList
{
	ref array<ref SK_Spot> Spots;
}

class SK_Spawner
{
	protected static ref array<ref SK_Spot> s_Spots;

	static void Start()
	{
		SK_Settings s = SK_Settings.Get();
		if (!s.SpawnUnderPaintings || s.SpawnCount <= 0)
			return;
		string path = "$mission:shashka/spots.json";
		if (!FileExist(path))
		{
			Print("[Shashka] no " + path + " (tools/spawns.py writes it): no sheaths under paintings");
			return;
		}
		SK_SpotList list;
		string error;
		if (!JsonFileLoader<SK_SpotList>.LoadFile(path, list, error) || !list || !list.Spots)
		{
			Print("[Shashka] (E) bad " + path + ": " + error);
			return;
		}
		s_Spots = list.Spots;
		Print(string.Format("[Shashka] %1 spots under paintings; keeping %2 sheaths there, checked every %3 min", s_Spots.Count(), s.SpawnCount, s.SpawnCheckMinutes));
		g_Game.GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Check, 60000, false);
	}

	static void Check()
	{
		SK_Settings s = SK_Settings.Get();
		array<SK_Spot> open = {};
		int held = 0;
		foreach (SK_Spot spot : s_Spots)
		{
			if (Occupied(spot.Pos))
				held++;
			else
				open.Insert(spot);
		}
		int added = 0;
		while (held + added < s.SpawnCount && open.Count() > 0)
		{
			int i = Math.RandomInt(0, open.Count());
			if (Spawn(open[i]))
				added++;
			open.Remove(i);
		}
		if (added > 0)
			Print(string.Format("[Shashka] %1 sheaths under paintings, %2 new", held + added, added));
		g_Game.GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(Check, s.SpawnCheckMinutes * 60000, false);
	}

	static bool Occupied(vector pos)
	{
		array<Object> objects = {};
		g_Game.GetObjectsAtPosition3D(pos, 0.6, objects, null);
		foreach (Object o : objects)
		{
			if (SK_Sheath.Cast(o))
				return true;
		}
		return false;
	}

	//! the floor under a spot: the spots are measured from the painting, whose origin isn't quite at floor level
	static vector FloorAt(vector pos)
	{
		vector hit, dir;
		int comp;
		if (DayZPhysics.RaycastRV(pos + "0 1.0 0", pos - "0 2.0 0", hit, dir, comp, null, null, null, false, false, ObjIntersectGeom))
			return hit;
		return pos;
	}

	//! a sheath standing on its chape under the painting, leaning back on the wall, the shashka in it. Placed as is,
	//! without physics: dropped, it would fall over
	static SK_Sheath Spawn(SK_Spot spot)
	{
		vector floor = FloorAt(spot.Pos);
		SK_Sheath sheath = SK_Sheath.Cast(g_Game.CreateObjectEx("SK_Sheath", floor, ECE_NONE));
		if (!sheath)
			return null;
		vector wall = spot.Wall;
		if (wall.Length() < 0.1)
			wall = "0 0 1";
		sheath.SetDirection(wall);
		vector ori = sheath.GetOrientation();
		ori[1] = -12;
		sheath.SetOrientation(ori);
		sheath.SetPosition(floor - sheath.VectorToParent(SK_SHEATH_CHAPE));	// the chape on the floor
		sheath.GetInventory().CreateAttachment("SK_Shashka");
		return sheath;
	}
}
