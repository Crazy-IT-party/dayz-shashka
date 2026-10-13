# Shashka

<img src="https://cdn.simpleicons.org/claude" alt="Claude Code" height="16"> [Hecho por Claude Code con el plugin `universal-modder`](https://github.com/rehan-remade/universal-modder)

[![made with universal-modder](https://raw.githubusercontent.com/rehan-remade/universal-modder/main/docs/media/made-with-dark.svg)](https://github.com/rehan-remade/universal-modder)

[English](README.md) · [Русский](README-RU.md) · **Español** · [Português](README-PT.md)

**[Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3818636663)** · **[Vídeo (YouTube)](https://youtu.be/jrHFKSWTluk)**

<table>
<tr><td align="center"><a href="docs/screenshots/01_blade.jpg"><img src="docs/screenshots/01_blade_thumb.jpg" width="400" alt="En la mano"></a><br><sub>En la mano</sub></td><td align="center"><a href="docs/screenshots/02_cut.jpg"><img src="docs/screenshots/02_cut_thumb.jpg" width="400" alt="Un tajo"></a><br><sub>Un tajo</sub></td></tr>
<tr><td align="center"><a href="docs/screenshots/03_painting.jpg"><img src="docs/screenshots/03_painting_thumb.jpg" width="400" alt="Bajo el cuadro"></a><br><sub>Bajo el cuadro</sub></td><td align="center"><a href="docs/screenshots/04_painting_wide.jpg"><img src="docs/screenshots/04_painting_wide_thumb.jpg" width="400" alt="Dónde encontrarla"></a><br><sub>Dónde encontrarla</sub></td></tr>
</table>

Un mod para DayZ: una shashka de estilo caucásico (guarniciones de plata con nielado, tres acanaladuras) que mata a
cualquiera de un solo tajo, se desgasta con las muertes que causa y se vuelve a afilar con una piedra, y su vaina de
cuero, que se lleva en el lado izquierdo del cinturón. Las vainas con la hoja dentro aparecen bajo el cuadro de
soldados a la carga en las casas de pueblo.

Mod de cliente + servidor `@Shashka`. Modelos, texturas y materiales de daño propios; las animaciones y el agarre
son los del machete.

## Qué hace

- **El tajo:** un golpe ligero o pesado mata a jugadores, infectados y animales (el número de golpes es
  configurable: cada uno quita 1/N de la salud total del objetivo además del daño de la propia hoja). La muerte se
  atribuye al atacante.
- **Alcance:** mayor que el del machete; el servidor envía sus valores a cada cliente al conectarse.
- **Desgaste por muertes:** blandirla no la mella, matar sí — dañada tras N muertes, muy dañada tras N × 1,7,
  arruinada tras N × 3 (la cuenta se guarda en el objeto). La fuerza del tajo en cada estado es configurable; por defecto una hoja arruinada solo hace el daño del machete.
- **Piedra de afilar:** la receta estándar «Afilar» la sube un nivel (muy dañada → dañada → impecable) y gasta una
  parte fija de la piedra. Una hoja arruinada no se puede afilar.
- **Vaina:** `SK_Sheath` cuelga del lado izquierdo del cinturón (`Belt_Left`), va a la espalda (hombro) o en la correa
  de una mochila (no de una bolsa de lona, de mensajero ni bandolera), y guarda la hoja, con la empuñadura a la vista. De los cinturones estándar, el militar la muestra; el de cuero no muestra ese espacio en absoluto.
- **Otros espacios:** la hoja desnuda a la espalda (cuerpo a cuerpo / hombro) o en la correa de una mochila,
  empuñadura arriba — todos desactivados por defecto.
- **Aparición:** vainas con la hoja dentro, de pie bajo el cuadro de soldados a la carga en las casas de pueblo;
  el propio mod las coloca y las repone.
- **Traducciones:** los trece idiomas de DayZ.

## Contenido

- `mod/Shashka` — el addon: config, scripts, modelos (MLOD `.p3d`), texturas (`.paa`), materiales (`.rvmat`) y la
  stringtable. Empaquétalo en un pbo con el prefijo `Shashka` con la herramienta que prefieras y fírmalo con tu
  clave.
- `mod/mod.cpp` — nombre y autor del mod, para la carpeta `@Shashka`.
- `mod/shashka.json` — los ajustes del servidor con sus valores por defecto.
- `missions/<mapa>/shashka` — los puntos de aparición para los mapas estándar: Chernarus (358 puntos), Livonia
  (190), Sakhal (99).

## Servidor

1. Crea la carpeta `@Shashka` — `addons/shashka.pbo` (y su `.bisign`), `mod.cpp`, `keys/` con tu `.bikey` —,
   ponla en la carpeta del servidor y cárgala en el servidor y en los clientes (`-mod=...;@Shashka`).
2. Ajustes: copia `mod/shashka.json` a `@Shashka/shashka.json` en la carpeta del servidor (se lee como
   `$CurrentDir:@Shashka/shashka.json`, así que la carpeta tiene que llamarse así ahí). Sin él, el servidor lee
   `$profile:Shashka/shashka.json` y escribe ahí los valores por defecto la primera vez. Reinicia para aplicarlos.

| clave | por defecto | |
|---|---|---|
| `KillsToDamaged` | 10 | N: muertes antes de que la hoja quede dañada |
| `BadlyDamagedFactor` | 1.7 | muy dañada tras N × esto muertes |
| `RuinedFactor` | 3.0 | arruinada tras N × esto muertes |
| `WhetstoneCostPercent` | 25 | parte de la piedra que gasta un afilado |
| `LightHitsToKill` / `HeavyHitsToKill` | 1 / 1 | golpes que matan a cualquiera (el pesado incluye el ataque en carrera) |
| `RangeLight` / `RangeHeavy` / `RangeSprint` | 1.9 / 1.9 / 3.8 | alcance en metros (machete: 1,4 / 1,4 / 3,3) |
| `DamagePristine` / `DamageWorn` / `DamageDamaged` / `DamageBadlyDamaged` / `DamageRuined` | 1 / 1 / 1 / 1 / 0 | parte de la salud total del objetivo que quita un tajo en ese estado de la hoja (dividida entre los golpes); 1 = mata de un tajo, 0 = solo el daño del machete |
| `AllowBelt` | 1 | la vaina en un cinturón |
| `AllowMeleeSlot` / `AllowShoulderSlot` | 0 / 0 | la hoja desnuda a la espalda |
| `AllowBackpackSlot` | 0 | la hoja desnuda en la correa de una mochila |
| `AllowSheathShoulder` / `AllowSheathBackpack` | 1 / 1 | la vaina, con la hoja dentro, a la espalda (hombro) / en la correa de una mochila |
| `SpawnUnderPaintings` | 1 | vainas bajo el cuadro de los soldados |
| `SpawnCount` | 4 | cuántos de esos puntos tienen una vaina a la vez |
| `SpawnCheckMinutes` | 30 | cada cuánto las repone el servidor |

3. Aparición: copia `missions/<mapa>/shashka` en la carpeta de tu misión (junto a `init.c`) y añádela al
   `cfgeconomycore.xml` de la misión, dentro de `<economycore>`:

   ```xml
   <ce folder="shashka">
       <file name="types.xml" type="types" />
   </ce>
   ```

   `spots.json` guarda las posiciones en el mundo bajo cada uno de esos cuadros en ese mapa; `types.xml` da a los
   objetos su tiempo de vida (nominal 0 — la economía no los crea, lo hace el mod). Sin `spots.json`, simplemente
   no aparecen.

## Créditos

- El aspecto de la hoja, la empuñadura y las guarniciones: una shashka caucásica de la Livrustkammaren, Estocolmo
  (inv. 1315), de
  [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Sabel,_schaschka_-_Livrustkammaren_-_1315_(cropped).tif)
  (CC0). La foto es en blanco y negro: sus luces y sombras dan el ornamento; los colores son nuestros.
- Materiales fotográficos: [ambientCG](https://ambientcg.com) (CC0) — Metal009, Leather037, Metal056B.

## Licencia

Código: [The Unlicense](LICENSE) — dominio público, haz con él lo que quieras. Las fotos de las que se hicieron las texturas son CC0 (ver Créditos).
