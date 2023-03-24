import discord
from discord.ext import commands
import random
import pickle
import time
import threading
import asyncio

token='TOKEN_HERE'
alive=True

pclass_index={'warrior': 0, 'rogue': 1, 'wizard': 2}
pclass_inverse_index={0: 'Warrior', 1: 'Rogue', 2: 'Wizard'}

#name, hp, ac, sides, times, hit bonus
monster_index=((('Goblin', 9, 10, 4, 1, 0), ('Grey Wolf', 8, 10, 4, 1, 1), ('Zombie', 12, 8, 6, 1, -1), ('Kobold', 7, 10, 4, 1, 0), ('Bandit', 8, 11, 6, 1, 1), ('Giant Spider', 5, 12, 4, 1, 2)), #lvl 1-2
               (('Orc', 14, 11, 8, 1, 2), ('Ghoul', 16, 9, 8, 1, 1), ('Dancing Sword', 9, 14, 6, 1, 2), ('Harpy', 12, 13, 4, 2, 2), ('Dire Wolf', 13, 12, 4, 2, 2), ('Bugbear', 15, 11, 4, 2, 2)), #lvl 3-4
               (('Werewolf', 26, 14, 6, 2, 3), ('Troll', 30, 15, 6, 2, 3), ('Wight', 22, 13, 6, 2, 2), ('Ghost', 18, 17, 6, 2, 2), ('Hill Giant', 33, 14, 12, 1, 2), ('Ogre', 25, 14, 6, 2, 3)), #lvl 5-6
               (('Wyvern', 30, 17, 4, 4, 4), ('Young Dragon', 37, 17, 4, 3, 5), ('Water Elemental', 40, 16, 8, 2, 5), ('Stone Golem', 50, 12, 10, 2, 3), ('Minotaur', 36, 15, 8, 2, 4), ('Fire Giant', 36, 15, 8, 2, 4)), #lvl 7-8
               (('Dragon', 65, 25, 8, 3, 7), ('Cloud Giant', 60, 21, 12, 2, 7), ('Fire Elemental', 50, 22, 6, 3, 6), ('Hydra', 58, 28, 6, 3, 7), ('Manticore', 50, 30, 20, 1, 7), ('Gorgon', 50, 21, 12, 3, 4))) #lvl 9-10

#name, sides/ac/spell level, rolls/none/spell index, type 0=ac 1=weap 2=food 3=spell, price, mod
shop_index=(('Quilted Armor', 11, None, 0, 75, 0),
            ('Leather Armor', 12, None, 0, 125, 0),
            ('Splint Mail', 13, None, 0, 200, 0),
            ('Chain Mail', 14, None, 0, 300, 0),
            ('Plate Mail', 15, None, 0, 400, 0),
            ('Long Sword', 8, 1, 1, 100, 0),
            ('Axe', 10, 1, 1, 175, 0),
            ('Halberd', 12, 1, 1, 225, 0),
            ('Two-Handed Sword', 8, 2, 1, 375, 0),
            ('Rations', 10, None, 2, 8, 0),
            ('Iron Rations', 20, None, 2, 18, 0))

#name, die sides, time, type 0=dps 1=ac buff 2=dmg buff 3=hit buff
all_spells=((('Magic Missile', 4, 2, 0), ('Shield', 4, 1, 1), ('Focus', 4, 1, 3), ('Weapon Enchantment', 4, 1, 2)),
            (('Blur', 4, 2, 1), ('Fireball', 6, 3, 0), ('ESP', 4, 2, 3), ('Fiery Blade', 4, 2, 2)),
            (('Invisibility', 4, 3, 1), ('Chain Lightning', 6, 5, 0), ('Ethereal Weapon', 6, 2, 2), ('Clairvoynace', 4, 3, 3)))

def dice(side=6, times=1):
    total=0
    for x in range(times):
        total+=random.randrange(1, side)
    return total
class Game:
    def __init__(self):
        self.players={}
    def find_player(self, name):
        try:
            p=self.players[name]
            return p
        except:
            return False
    def add_player(self, name, pclass):
        p=self.Player(name, pclass)
        self.players[name]=p
        return p
    def dead(self, p):
        try:
            print(p.name+' has died!')
            del self.players[p.name]
        except:
            pass
    class Player:
        def __init__(self, name, pclass):
            self.pclass=pclass
            self.duel=None
            self.mon=None
            self.battle=False
            self.inv=[['Short Sword', 6, 1, 1, 50, 0], ['Cloth', 10, None, 0, 20, 0], None, None, None, None, None, None, None, None]
            self.invCount=2
            self.name=name
            self.xp=0
            self.xpmax=40
            self.lvl=1
            self.str=dice(8, 2)+2
            self.dex=dice(8, 2)+2
            self.vit=dice(8, 2)+2
            self.intel=dice(8, 2)+2
            if pclass == pclass_index['warrior']:
                self.str=max(10, self.str)+2
            elif pclass == pclass_index['rogue']:
                self.dex=max(10, self.dex)+2
            elif pclass == pclass_index['wizard']:
                self.intel=max(10, self.intel)+2
            self.spells=[]
            self.spell_book=[[['Magic Missile', 4, 2, 0], ['Shield', 4, 1, 1], ['Focus', 4, 1, 3], ['Weapon Enchantment', 4, 1, 2]],
                             [['Blur', 4, 2, 1], ['Fireball', 6, 3, 0], ['ESP', 4, 2, 3], ['Fiery Blade', 4, 2, 2]],
                             [['Invisibility', 4, 3, 1], ['Chain Lightning', 6, 5, 0], ['Ethereal Weapon', 6, 2, 2], ['Clairvoynace', 4, 3, 3]]]
            if self.pclass == pclass_index['wizard']:
                new=random.choice(self.spell_book[0])
                self.spells.append(new)
                self.spell_book[0].remove(new)
            else:
                roll=dice(4, 1)-1
                item=['Scroll of '+all_spells[int(self.lvl/4)][roll][0], int(self.lvl/4), roll, 3, int((self.lvl/4)+1)*55]
                self.add_item(item)
            self.q_weap=0
            self.q_ac=1
            self.gold=dice(6, 4)*10
            self.hpmax=10+int((self.vit-10)/2)
            self.hp=self.hpmax
            self.spell_bonus=int((self.intel-10)/2)
            self.turns=1 #total turns
            self.attacks=1 #attack moves per turn
            self.spell_points=1 #spell points per encounter
            self.apply()
        def add_item(self, item):
            if self.invCount < len(self.inv):
                for i in range(len(self.inv)):
                    if not self.inv[i]:
                        self.inv[i]=item
                        self.invCount+=1
                        return True
            else:
                return False
        def remove_item(self, index):
            if index < len(self.inv) and index >= 0 and self.inv[index] != None:
                self.inv[index]=None
                return True
            else:
                return False
        def encounter(self):
            self.apply()
            select=dice(10, 1)-1
            if select >= 7:
                g=dice(6, 4)*3
                x=dice(6, 3)*int((self.lvl+1)/2)
                out='***Found Treasure!***\n+'+str(g)+' Gold!\n+'+str(x)+' XP!\n'
                self.gold+=g
                self.xp+=x
                spawn=dice(6, 1)
                if spawn <= 4:
                    i=dice(8, 1)
                    if i <= 5:
                        roll=dice(4, 1)-1
                        item=['Scroll of '+all_spells[int(self.lvl/4)][roll][0], int(self.lvl/4), roll, 3, int((self.lvl/4)+1)*55]
                    else:
                        roll=dice(9, 1)-1
                        item=[*shop_index[roll]]
                        mod=random.choice([1, 1, 1, 1, 2, 2, 3])
                        item[5]=mod
                        item[4]+=mod*20
                        item[0]+=' +'+(str(mod))
                    if (self.add_item(item)):
                        out+='Found **'+item[0]+'!**'
            else:
                self.battle=True
                self.mon=self.Monster(int((self.lvl-1)/2), select)
                out='Encountered **'+self.mon.name+'!**'
            return out
        def apply(self):
            #refresh data
            self.sp=self.spell_points
            self.turn=self.turns
            self.count=0
            self.ac_buff=0
            self.hit_buff=0
            self.dmg_buff=0
            self.buffs=[]
            self.dmg_bonus=int((self.str-10)/2)+self.inv[self.q_weap][5]
            self.hit_bonus=int((self.dex-10)/2)+int(self.lvl/3)+self.inv[self.q_weap][5]
            self.ac=int(self.inv[self.q_ac][1]+(self.dex-10)/2)+self.inv[self.q_ac][5]
        def levelup(self):
            if self.lvl == 10:
                self.xp=0
                return
            self.lvl+=1
            if self.pclass == pclass_index['warrior']: #strength proficent
                self.attacks=int(self.lvl/3)+1
            if self.pclass == pclass_index['rogue']: #agility proficent
                self.turns=int(self.lvl/4)+1
            if self.pclass == pclass_index['wizard']: #magic proficent
                self.spell_bonus=int((self.intel-10)/2)+int(self.lvl/3)
                new=random.choice(self.spell_book[int(self.lvl/4)])
                self.spells.append(new)
                self.spell_book[int(self.lvl/4)].remove(new)
                self.spell_points=int(self.lvl/3)+1
            self.xp-=self.xpmax
            self.xpmax*=1.5
            self.xpmax=int(self.xpmax)
            self.hpmax+=int(dice(10, 1)+(self.vit-10)/2)
            self.hp=self.hpmax
        class Monster: #used as structure for easy addressing
            def __init__(self, mlvl, select):
                self.name=monster_index[mlvl][select][0]
                self.hp=monster_index[mlvl][select][1]
                self.ac=monster_index[mlvl][select][2]
                self.roll_sides=monster_index[mlvl][select][3]
                self.roll_times=monster_index[mlvl][select][4]
                self.hit_bonus=monster_index[mlvl][select][5]

async def show_stats(p):
    if True:
        if p.hit_bonus >= 0:
            hit_bonus='+'+str(p.hit_bonus+p.hit_buff)
        else:
            hit_bonus=str(p.hit_bonus)
        if p.spell_bonus >= 0:
            spell_bonus='+'+str(p.spell_bonus)
        else:
            spell_bonus=str(p.spell_bonus)
        if p.dmg_bonus >= 0:
            dmg_bonus='+'+str(p.dmg_bonus+p.dmg_buff)
        else:
            dmg_bonus=str(p.dmg_bonus+p.dmg_buff)
        if p.attacks > 1:
            atk=' Attacks'
        else:
            atk=' Attack'
        if p.turns > 1:
            t=' Turns'
        else:
            t=' Turn'
        out='```'
        out+=p.name
        out+='\'s Character:\nLevel: '+str(p.lvl)
        out+='\nClass: '+pclass_inverse_index[p.pclass]
        out+='\nLife: '+str(p.hp)+'/'+str(p.hpmax)
        out+='\nArmor: '+p.inv[p.q_ac][0]+' +'+str(p.ac)
        out+='\nAttack: '+p.inv[p.q_weap][0]+' '+str(p.inv[p.q_weap][2])+'d'+str(p.inv[p.q_weap][1])+dmg_bonus+' '+hit_bonus+' To Hit x'+str(p.attacks)+atk
        out+='\nExperience: '+str(p.xp)+'/'+str(p.xpmax)
        out+='\nStrength: '+str(p.str)+'\nDexterity: '+str(p.dex)+'\nVitality: '+str(p.vit)
        out+='\nIntelligence: '+str(p.intel)+' '+spell_bonus+' Spell Power\n'
        out+=str(p.turns)+t+' per move```'
        return out
    else:
        return '***ERROR!***'

main=Game()
intents=discord.Intents.default()
intents.message_content=True
dm=commands.Bot(command_prefix='$', case_insensitive=True, intents=intents)

@dm.event
async def on_ready():
    print('Dungeon Master is ready!')

@dm.command()
async def equip(ctx, equip):
    a=str(ctx.message.author)
    p=main.find_player(a)
    e=int(equip)
    if p.inv[e]:
        if p.inv[e][3] == 0:
            p.q_ac=e
            await ctx.send('Equipped **'+p.inv[e][0]+'**')
        elif p.inv[e][3] == 1:
            p.q_weap=e
            await ctx.send('Equipped **'+p.inv[e][0]+'**')
        else:
            await ctx.send('Unable to equip that!')
        p.apply()
    else:
        await ctx.send('***Invalid Item!***')

@dm.command()
async def newchar(ctx, pclass=None):
    a=str(ctx.message.author)
    #test=main.find_player(a)
    test=False
    bad=False
    if test:
        await ctx.send('You already have a character!')
        return
    else:
        try:
            pclass=str(pclass)
            if pclass_index[pclass] >= 0 and pclass_index[pclass] < 3:
                p=main.add_player(a, pclass_index[pclass])
                print('Created Character for', a)
                out=await show_stats(p)
                await ctx.send('Created your Character!\n'+out)
            else:
                bad=True
        except:
            bad=True
    if bad:
        await ctx.send('**Invalid Class!**\nValid Classes are: ```$newchar warrior\n$newchar rogue\n$newchar wizard```')
@dm.command()
async def action(ctx, *args):
    a=str(ctx.message.author)
    p=main.find_player(a)
    if not p:
        await ctx.send('You do not have a character!')
        return
    #healing allowed out of combat
    elif args[0] == 'use' and p.battle == False:
        item=int(args[1])
        if item >= len(p.inv):
            await ctx.send('***Invalid Item!***')
            return
        elif p.inv[item][3] != 2:
            await ctx.send('***Cannot use that item right now!***')
            return
        else:
            p.hp+=p.inv[item][1]
            if p.hp > p.hpmax:
                p.hp=p.hpmax
            await ctx.send('Used **'+p.inv[item][0]+'!**')
            p.remove_item(item)
            return
    if not p.battle:
        await ctx.send('You are not in combat!')
        return
    #basic attack
    if args[0] == 'attack':
        p.turn-=1
        damage=0
        for i in range(p.attacks):
            if p.mon.hp <= 0:
                break
            else:
                hit=dice(20, 1)+p.hit_bonus+p.hit_buff
                if hit >= p.mon.ac:
                    h=dice(p.inv[p.q_weap][1], p.inv[p.q_weap][2])+p.dmg_bonus+p.dmg_buff
                    if h < 1:
                        h=1
                    damage+=h
                    await ctx.send('You hit the **'+p.mon.name+'** for **'+str(h)+'** damage!')
                else:
                    await ctx.send('You **Missed!**')
                p.mon.hp-=damage
    #spells
    elif args[0] == 'cast':
        spell=int(args[1])
        if spell >= len(p.spells):
            await ctx.send('***Invalid Spell!***')
            return
        elif p.spells[spell]:
            p.turn-=1
            cost=int(spell/3)+1
            if not p.sp >= cost:
                await ctx.send('Not enough spell points!')
                return
            if not p.spells[spell][3] in p.buffs:
                p.sp-=cost
                add=dice(p.spells[spell][1], p.spells[spell][2])
                add+=p.spell_bonus
                if add < 1:
                    add=1
                if p.spells[spell][3] != 0:
                    p.buffs.append(p.spells[spell][3])
                out='You Cast **'+p.spells[spell][0]+'!**\n'
                if p.spells[spell][3] == 0: #dps
                    p.mon.hp-=add
                    out+='Hit the **'+p.mon.name+'** for **'+str(add)+'** damage!'
                elif p.spells[spell][3] == 1: #ac
                    p.ac+=add
                    out+='**+'+str(add)+' AC**'
                elif p.spells[spell][3] == 2: #dmg
                    p.dmg_bonus+=add
                    out+='**+'+str(add)+' Damage**'
                elif p.spells[spell][3] == 3: #hit
                    p.hit_bonus+=add
                    out+='**+'+str(add)+' to Hit**'
                await ctx.send(out)
            else:
                await ctx.send('**You already have a similar spell active!**')
    #use
    elif args[0] == 'use':
        item=int(args[1])
        if item >= len(p.inv):
            await ctx.send('***Invalid Item!***')
            return
        elif p.inv[item][3] != 2 and p.inv[item][3] != 3 and p.inv[item][3] != 4 and p.inv[item][3] != 5 and p.inv[item][3] != 6:
            await ctx.send('***Cannot use that item!***')
            return
        else:
            p.turn-=1
            if p.inv[item][3] == 2:
                p.hp+=p.inv[item][1]
                if p.hp > p.hpmax:
                    p.hp=p.hpmax  
                await ctx.send('Used **'+p.inv[item][0]+'!** **+'+str(p.inv[item][1])+'HP**')
                #shift correction
                if p.q_weap > item:
                    p.q_weap-=1
                if p.q_ac > item:
                    p.q_ac-=1
                p.remove_item(item)
            elif p.inv[item][3] == 3:
                spell=all_spells[p.inv[item][1]][p.inv[item][2]]
                if not spell[3] in p.buffs:
                    add=dice(spell[1], spell[2])
                    add+=p.spell_bonus
                    if add < 1:
                        add=1
                    if spell[3] != 0:
                        p.buffs.append(spell[3])
                    out='You Cast **'+spell[0]+'!**\n'
                    if spell[3] == 0: #dps
                        p.mon.hp-=add
                        out+='Hit the **'+p.mon.name+'** for **'+str(add)+'** damage!'
                    elif spell[3] == 1: #ac
                        p.ac_buff+=add
                        out+='**+'+str(add)+' AC**'
                    elif spell[3] == 2: #dmg
                        p.dmg_buff+=add
                        out+='**+'+str(add)+' Damage**'
                    elif spell[3] == 3: #hit
                        p.hit_buff+=add
                        out+='**+'+str(add)+' to Hit**'
                    await ctx.send(out)
                    #shift correction
                    if p.q_weap > item:
                        p.q_weap-=1
                    if p.q_ac > item:
                        p.q_ac-=1
                    p.remove_item(item)
                else:
                    await ctx.send('**You already have a similar spell active!**')
    elif args[0] == 'flee':
        flee=random.choice([False, False, True])
        if flee:
            p.battle=False
            p.apply()
            await ctx.send('*You flee from battle!*')
            return
        else:
            p.turn-=1
            await ctx.send('**Failed attempt to flee!**')
    else:
        await ctx.send('**Please choose a valid action!**\n```\n$action attack\n$action cast [spell number]\n$action use [item number]\n$action flee```')
    #win
    if p.mon.hp < 1:
        xp_reward=int((p.lvl+1)/2)*dice(4, 4)
        gold_reward=int((p.lvl+1)/2)*int(dice(6, 4)*1.2)
        await ctx.send('Defeated the **'+p.mon.name+'!**\n**+'+str(xp_reward)+' XP!**\n**+'+str(gold_reward)+' Gold!**')
        p.xp+=xp_reward
        p.gold+=gold_reward
        p.battle=False
        p.apply()
        if p.xp >= p.xpmax:
            p.levelup()
            out='***LEVEL UP!***\n'
            out+=await show_stats(p)
            await ctx.send(out)
        return
    #monster turn
    if p.turn < 1:
        monhit=dice(20, 1)+p.mon.hit_bonus
        if monhit >= p.ac+p.ac_buff:
            mondmg=dice(p.mon.roll_sides, p.mon.roll_times)
            p.hp-=mondmg
            await ctx.send('The **'+p.mon.name+'** hit you for **'+str(mondmg)+'** damage!\n**'+str(p.hp)+'** Life remaining!')
        else:
            await ctx.send('The **'+p.mon.name+'** Missed!')
        p.turn=p.turns
    #dead
    if p.hp < 1:
        main.dead(p)
        await ctx.send('***You have been slain!***\n*You will need to create a new character...*')
@dm.command()
async def encounter(ctx):
    a=str(ctx.message.author)
    p=main.find_player(a)
    if not p:
        await ctx.send('You do not have a character!')
        return
    elif p.battle:
        await ctx.send('You are already in a battle!')
        return
    out=p.encounter()
    await ctx.send(out)
    if p.xp >= p.xpmax:
        p.levelup()
        out='***LEVEL UP!***\n'
        out+=await show_stats(p)
        await ctx.send(out)
@dm.command()
async def stats(ctx):
    a=str(ctx.message.author)
    p=main.find_player(a)
    out='You do not have a character!'
    if p:
        out=await show_stats(p)
    await ctx.send(out)

@dm.command()
async def spellbook(ctx):
    a=str(ctx.message.author)
    p=main.find_player(a)
    out='You do not have a character!'
    if p:
        if p.pclass != pclass_index['wizard']:
            out='You must be a Wizard to learn spells, you must use scrolls instead!'
        else:
            out='```Known Spells:\n'
            count=0
            for spell in p.spells:
                out+=str(count)+': '
                if spell[3] == 0:
                    out+=spell[0]+' '+str(spell[2])+'d'+str(spell[1])+' Damage'
                elif spell[3] == 1:
                    out+=spell[0]+' +'+str(spell[2])+'d'+str(spell[1])+' AC'
                elif spell[3] == 2:
                    out+=spell[0]+' +'+str(spell[2])+'d'+str(spell[1])+' Weapon Damage'
                elif spell[3] == 3:
                    out+=spell[0]+' +'+str(spell[2])+'d'+str(spell[1])+' to Hit'
                out+=' SP: '+str(int(count/3+1))+'\n'
                count+=1
            out+='\n'+str(p.spell_points)+' Spell Point(s) per encounter```'
    await ctx.send(out)
@dm.command()
async def buy(ctx, i):
    a=str(ctx.message.author)
    p=main.find_player(a)
    if p:
        if p.battle:
            await ctx.send('You are in combat!')
            return
        try:
            buy=shop_index[int(i)]
            if p.gold < buy[4]:
                await ctx.send('Not enough gold!')
                return
            else:
                p.add_item(buy)
                p.gold-=buy[4]
                await ctx.send('Bought ***'+buy[0]+'***')
        except:
            await ctx.send('Invalid Item!')
    else:
        await ctx.send('You do not have a character!')
@dm.command()
async def sell(ctx, i):
    g=str(ctx.guild)
    a=str(ctx.message.author)
    p=main.find_player(a)
    i=int(i)
    if p:
        if not p.battle:
            if i < len(p.inv):
                if i == p.q_weap or i == p.q_ac:
                    await ctx.send('Cannot sell equipped item!')
                    return
                p.gold+=int(p.inv[i][4]/2)
                await ctx.send('Sold **'+p.inv[i][0]+'!**')
                p.remove_item(i)
            else:
                await ctx.send('***Invalid Item!***')
        else:
            await ctx.send('You are in combat!')
    else:
        await ctx.send('You do not have a character!')
@dm.command()
async def shop(ctx):
    out='```Shop:\n'
    c=0
    for item in shop_index:
        out+=str(c)+': '+item[0]
        if item[3] == 0:
            out+=' '+str(item[1])+' AC'
        elif item[3] == 1:
            out+=' '+str(item[2])+'d'+str(item[1])+' Damage'
        elif item[3] == 2:
            out+=' +'+str(item[1])+' Healing'
        c+=1
        out+=' '+str(item[4])+'g\n'
    out+='```'
    await ctx.send(out)

@dm.command()
async def inv(ctx):
    a=str(ctx.message.author)
    out='You do not have a character!'
    p=main.find_player(a)
    if p:
        i=0
        out='```Your Items:\n'
        for item in p.inv:
            if item != None: 
                out+=str(i)+': '+item[0]
                if item[3] == 0:
                    out+=' '+str(item[1])+' AC\n'
                elif item[3] == 1:
                    out+=' '+str(item[2])+'d'+str(item[1])+' Damage\n'
                elif item[3] == 2:
                    out+=' +'+str(item[1])+' Healing\n'
                elif item[3] == 3:
                    spell=all_spells[item[1]][item[2]]
                    if spell[3] == 0:
                        out+=' '+str(spell[2])+'d'+str(spell[1])+' Damage\n'
                    elif spell[3] == 1:
                        out+=' +'+str(spell[2])+'d'+str(spell[1])+' AC\n'
                    elif spell[3] == 2:
                        out+=' +'+str(spell[2])+'d'+str(spell[1])+' Weapon Damage\n'
                    elif spell[3] == 3:
                        out+=' +'+str(spell[2])+'d'+str(spell[1])+' to Hit\n'
            i+=1
        out+='Gold: '+str(p.gold)+'```'
    await ctx.send(out)
@dm.command()
@commands.is_owner()
async def save(ctx):
    save_all()
    await ctx.send('*Saved all characters!*')
@dm.command()
@commands.is_owner()
async def logout(ctx):
    global alive
    alive=False
    print('Waiting to logout...')
    await ctx.send('*Saving and logging out...*')
    await dm.close()
def save_all():
    f=open('dm.sv', 'wb')
    pickle.dump(main, f)
    f.close()
def save_loop():
    mins=10
    factor=2
    print('Saves every '+str(mins)+' minutes and waits '+str(int(mins/factor))+' seconds to logout.\n')
    while alive:
        for i in range(60*factor):
            if not alive:
                break
            else:
                time.sleep(mins/factor)
        save_all()
        print('\nSaved.\n')

if __name__ == '__main__':
    t=threading.Thread(target=save_loop)
    t.start()
    try:
        f=open('dm.sv', 'rb')
        main=pickle.load(f)
        print('Loaded save file!')
    except:
        print('No save file found.')
    dm.run(token)
