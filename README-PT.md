# Shashka

<img src="https://cdn.simpleicons.org/claude" alt="Claude Code" height="16"> [Feito pelo Claude Code com o plugin `universal-modder`](https://github.com/rehan-remade/universal-modder)

[![made with universal-modder](https://raw.githubusercontent.com/rehan-remade/universal-modder/main/docs/media/made-with-dark.svg)](https://github.com/rehan-remade/universal-modder)

[English](README.md) · [Русский](README-RU.md) · [Español](README-ES.md) · **Português**

**[Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3818636663)** · **[Vídeo (YouTube)](https://youtu.be/jrHFKSWTluk)**

<table>
<tr><td align="center"><a href="docs/screenshots/01_blade.jpg"><img src="docs/screenshots/01_blade_thumb.jpg" width="400" alt="Na mão"></a><br><sub>Na mão</sub></td><td align="center"><a href="docs/screenshots/02_cut.jpg"><img src="docs/screenshots/02_cut_thumb.jpg" width="400" alt="Um golpe"></a><br><sub>Um golpe</sub></td></tr>
<tr><td align="center"><a href="docs/screenshots/03_painting.jpg"><img src="docs/screenshots/03_painting_thumb.jpg" width="400" alt="Sob o quadro"></a><br><sub>Sob o quadro</sub></td><td align="center"><a href="docs/screenshots/04_painting_wide.jpg"><img src="docs/screenshots/04_painting_wide_thumb.jpg" width="400" alt="Onde encontrá-la"></a><br><sub>Onde encontrá-la</sub></td></tr>
</table>

Um mod para DayZ: uma shashka de estilo caucasiano (guarnições de prata com nielo, três sulcos) que mata qualquer um
com um só golpe, se desgasta com as mortes que causa e volta a ser afiada numa pedra de amolar, e a sua bainha de
couro, usada no lado esquerdo do cinto. Bainhas com a lâmina dentro aparecem sob o quadro de soldados em carga nas
casas de aldeia.

Mod de cliente + servidor `@Shashka`. Modelos, texturas e materiais de dano próprios; as animações e a pega são as
do machete.

## O que faz

- **O golpe:** um golpe leve ou pesado mata jogadores, infetados e animais (o número de golpes é configurável:
  cada um tira 1/N da vida total do alvo, além do dano da própria lâmina). A morte é atribuída ao atacante.
- **Alcance:** maior que o do machete; o servidor envia os seus valores a cada cliente ao ligar.
- **Desgaste por mortes:** brandi-la não a embota, matar sim — danificada após N mortes, muito danificada após
  N × 1,7, arruinada após N × 3 (a contagem fica guardada no objeto). A força do golpe em cada estado é configurável; por defeito uma lâmina arruinada só faz o dano do machete.
- **Pedra de amolar:** a receita padrão «Afiar» sobe-a um nível (muito danificada → danificada → impecável) e gasta
  uma parte fixa da pedra. Uma lâmina arruinada não pode ser afiada.
- **Bainha:** `SK_Sheath` pendura-se no lado esquerdo do cinto (`Belt_Left`), vai às costas (ombro) ou na correia de
  uma mochila (não de uma bolsa de lona, de mensageiro nem a tiracolo), e guarda a lâmina, com o punho à vista. Dos cintos padrão, o militar mostra-a; o de couro não mostra esse espaço de todo.
- **Outros espaços:** a lâmina sem bainha às costas (corpo a corpo / ombro) ou na correia de uma mochila, punho para
  cima — todos desativados por defeito.
- **Aparecimento:** bainhas com a lâmina dentro, de pé sob o quadro de soldados em carga nas casas de aldeia; o
  próprio mod coloca-as e repõe-nas.
- **Traduções:** os treze idiomas do DayZ.

## Conteúdo

- `mod/Shashka` — o addon: config, scripts, modelos (MLOD `.p3d`), texturas (`.paa`), materiais (`.rvmat`) e a
  stringtable. Empacota-o num pbo com o prefixo `Shashka` com a ferramenta que preferires e assina-o com a tua
  chave.
- `mod/mod.cpp` — nome e autor do mod, para a pasta `@Shashka`.
- `mod/shashka.json` — as definições do servidor com os seus valores por defeito.
- `missions/<mapa>/shashka` — os pontos de aparecimento para os mapas padrão: Chernarus (358 pontos), Livonia (190),
  Sakhal (99).

## Servidor

1. Cria a pasta `@Shashka` — `addons/shashka.pbo` (e o seu `.bisign`), `mod.cpp`, `keys/` com a tua `.bikey` —,
   coloca-a na pasta do servidor e carrega-a no servidor e nos clientes (`-mod=...;@Shashka`).
2. Definições: copia `mod/shashka.json` para `@Shashka/shashka.json` na pasta do servidor (é lido como
   `$CurrentDir:@Shashka/shashka.json`, por isso a pasta tem de ter esse nome aí). Sem ele, o servidor lê
   `$profile:Shashka/shashka.json` e escreve lá os valores por defeito da primeira vez. Reinicia para aplicar.

| chave | por defeito | |
|---|---|---|
| `KillsToDamaged` | 10 | N: mortes até a lâmina ficar danificada |
| `BadlyDamagedFactor` | 1.7 | muito danificada após N × isto mortes |
| `RuinedFactor` | 3.0 | arruinada após N × isto mortes |
| `WhetstoneCostPercent` | 25 | parte da pedra gasta numa afiação |
| `LightHitsToKill` / `HeavyHitsToKill` | 1 / 1 | golpes que matam qualquer um (o pesado inclui o ataque em corrida) |
| `RangeLight` / `RangeHeavy` / `RangeSprint` | 1.9 / 1.9 / 3.8 | alcance em metros (machete: 1,4 / 1,4 / 3,3) |
| `DamagePristine` / `DamageWorn` / `DamageDamaged` / `DamageBadlyDamaged` / `DamageRuined` | 1 / 1 / 1 / 1 / 0 | parte da vida total do alvo que um golpe tira nesse estado da lâmina (dividida pelos golpes); 1 = mata de um golpe, 0 = só o dano do machete |
| `AllowBelt` | 1 | a bainha num cinto |
| `AllowMeleeSlot` / `AllowShoulderSlot` | 0 / 0 | a lâmina sem bainha às costas |
| `AllowBackpackSlot` | 0 | a lâmina sem bainha na correia de uma mochila |
| `AllowSheathShoulder` / `AllowSheathBackpack` | 1 / 1 | a bainha, com a lâmina dentro, às costas (ombro) / na correia de uma mochila |
| `SpawnUnderPaintings` | 1 | bainhas sob o quadro dos soldados |
| `SpawnCount` | 4 | quantos desses pontos têm uma bainha ao mesmo tempo |
| `SpawnCheckMinutes` | 30 | de quanto em quanto tempo o servidor as repõe |

3. Aparecimento: copia `missions/<mapa>/shashka` para a pasta da tua missão (ao lado de `init.c`) e acrescenta-a ao
   `cfgeconomycore.xml` da missão, dentro de `<economycore>`:

   ```xml
   <ce folder="shashka">
       <file name="types.xml" type="types" />
   </ce>
   ```

   `spots.json` guarda as posições no mundo sob cada um desses quadros nesse mapa; `types.xml` dá aos objetos o seu
   tempo de vida (nominal 0 — a economia não os cria, quem os cria é o mod). Sem `spots.json`, simplesmente não
   aparecem.

## Créditos

- O aspeto da lâmina, do punho e das guarnições: uma shashka caucasiana da Livrustkammaren, Estocolmo (inv. 1315),
  da
  [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Sabel,_schaschka_-_Livrustkammaren_-_1315_(cropped).tif)
  (CC0). A foto é a preto e branco: as suas luzes e sombras dão o ornamento; as cores são nossas.
- Materiais fotográficos: [ambientCG](https://ambientcg.com) (CC0) — Metal009, Leather037, Metal056B.

## Licença

Código: [The Unlicense](LICENSE) — domínio público, faz com ele o que quiseres. As fotos de que se fizeram as texturas são CC0 (ver Créditos).
