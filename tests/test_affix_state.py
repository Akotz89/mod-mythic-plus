"""Exercise affix methods against stubs on the project's guarded WSL host."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AffixStateTest(unittest.TestCase):
    def test_affix_state(self):
        subprocess.run(['/home/aaron/Documents/ChatGPT/wow private server/scripts/wow-build-host-guard'], check=True)
        text = (ROOT / 'src/mythic_affix.cpp').read_text()
        health = text[text.index('void HealthIncreaseAffix::HandleStaticEffect('):text.index('\nstd::string HealthIncreaseAffix::ToString()')]
        timer = text[text.index('void LightningSphereAffix::HandlePeriodicEffectMap('):text.index('\nstd::string LightningSphereAffix::ToString()')]
        map_header = (ROOT / 'src/mythic_plus.h').read_text()
        timer_field = next(line for line in map_header.splitlines() if 'lightningSphereTimers;' in line)
        source = r'''
#include <cassert>
#include <cstdint>
#include <list>
#include <unordered_map>
#include <vector>
using uint32=uint32_t;
#define ASSERT assert
constexpr int UNIT_MOD_HEALTH=0, BASE_VALUE=0, TEMPSUMMON_TIMED_OR_CORPSE_DESPAWN=0;
struct Creature { uint32 hp=50,max=100,create=100; float GetHealthPct(){return 100.f*hp/max;}
 void SetCreateHealth(uint32 v){create=v;} void SetMaxHealth(uint32 v){max=v;if(hp>max)hp=max;}
 uint32 GetMaxHealth(){return max;} void SetStatFlatModifier(int,int,float v){SetMaxHealth(uint32(v * 1.5f));} void SetHealth(uint32 v){hp=v;} void ResetPlayerDamageReq(){} };
struct MythicAffix {};
struct Player { bool isDead(){return false;} void SummonCreature(int,Player&,int,int){} };
struct Map { struct Entry { Player* GetSource() const{return nullptr;} };
 struct PlayerList { std::vector<Entry> entries; using const_iterator=std::vector<Entry>::const_iterator;
 bool IsEmpty() const{return entries.empty();} const_iterator begin() const{return entries.begin();} const_iterator end() const{return entries.end();} } players;
 PlayerList const& GetPlayers(){return players;} };
struct MythicPlus { struct CreatureData { uint32 originalMaxHealth=100; } creatureData;
 struct MapData { bool done=false;
''' + timer_field + r'''
 }; std::unordered_map<Map*,MapData> maps; static constexpr int NPC_LIGHTNING_SPHERE=1;
 CreatureData* GetCreatureData(Creature*,bool){return &creatureData;}
 bool IsMapInMythicPlus(Map* m){return maps.count(m)!=0;} MapData* GetMapData(Map* m,bool){return &maps.at(m);}
} manager; MythicPlus* sMythicPlus=&manager;
namespace Acore::Containers { Player* SelectRandomContainerElement(std::list<Player*> const& p){return p.front();} }
bool roll_chance_f(float){return false;}
struct HealthIncreaseAffix { float healthMod=1; bool CanApplyHealthIncrease(Creature*){return true;} void HandleStaticEffect(Creature*); };
struct LightningSphereAffix : MythicAffix { uint32 spawnTimerEnd=100; float chanceOfSpawn=0; void HandlePeriodicEffectMap(Map*,uint32); };
''' + health + '\n' + timer + r'''
int main(){
 Creature creature; HealthIncreaseAffix health; health.HandleStaticEffect(&creature);
 if(creature.max!=300 || creature.hp!=150) return 1;
 Map one,two; manager.maps[&one]={};manager.maps[&two]={};LightningSphereAffix affix;
 affix.HandlePeriodicEffectMap(&one,70);affix.HandlePeriodicEffectMap(&two,40);
 if(manager.maps[&one].lightningSphereTimers[&affix]!=70 || manager.maps[&two].lightningSphereTimers[&affix]!=40) return 2;
 affix.HandlePeriodicEffectMap(&one,40);affix.HandlePeriodicEffectMap(&one,1);
 if(manager.maps[&one].lightningSphereTimers[&affix]!=0 || manager.maps[&two].lightningSphereTimers[&affix]!=40) return 3;
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            cpp = Path(directory) / 'affix.cpp'
            cpp.write_text(source)
            binary = Path(directory) / 'affix'
            subprocess.run(['g++', '-std=c++17', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

if __name__ == '__main__':
    unittest.main()
