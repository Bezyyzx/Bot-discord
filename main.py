import discord
import os
import asyncpg
import json
from math import floor, sqrt
from discord.ui import Select, View
from discord.ext import commands
from discord import Embed
from flask import Flask
import threading
import asyncio
import random

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1396525966116917309
DATABASE_URL = os.getenv("DATABASE_URL")
ROLES_STATE_FILE = "roles_state.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

app = Flask('')

@app.route('/')
def home():
    return "Bot działa 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ----- SELECT VIEWS -----
class AgeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="17-19", description="Wiek 17-19"),
            discord.SelectOption(label="20-23", description="Wiek 20-23"),
            discord.SelectOption(label="24-27", description="Wiek 24-27"),
            discord.SelectOption(label="28+", description="Wiek 28+")
        ]
        super().__init__(placeholder="Wybierz swój przedział wiekowy", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        age_roles = ["17-19", "20-23", "24-27", "28+"]
        for role in interaction.user.roles:
            if role.name in age_roles:
                await interaction.user.remove_roles(role)

        selected_role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if selected_role:
            await interaction.user.add_roles(selected_role)
            await interaction.response.send_message(f"Nadano Ci rolę: **{selected_role.name}**", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nie udało się nadać roli.", ephemeral=True)

class AgeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(AgeSelect())

class GenderSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Mężczyzna", value="Mężczyzna", emoji="👨"),
            discord.SelectOption(label="Kobieta", value="Kobieta", emoji="👩")
        ]
        super().__init__(placeholder="Wybierz swoją płeć", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        selected_role_name = self.values[0]
        gender_roles = ["Mężczyzna", "Kobieta"]
        selected_role = discord.utils.get(guild.roles, name=selected_role_name)
        roles_to_remove = [discord.utils.get(guild.roles, name=r) for r in gender_roles if r != selected_role_name]
        await user.remove_roles(*filter(None, roles_to_remove))
        if selected_role:
            await user.add_roles(selected_role)
        await interaction.response.send_message(f"✅ Nadano Ci rolę **{selected_role_name}**.", ephemeral=True)

class GenderSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GenderSelect())

@bot.event
async def on_ready():
    print(f'✅ Bot jest online jako: {bot.user}')

    if not hasattr(bot, "db"):
        bot.db = await asyncpg.create_pool(DATABASE_URL)
        print("📡 Połączono z bazą danych!")

    role_channel_id = 1396550626262913166
    channel = bot.get_channel(role_channel_id)

    if not channel:
        print("❌ Nie znaleziono kanału do ról.")
        return

    if not has_sent_role_messages():
        try:
            await channel.send("**🎯 Wybierz swój przedział wiekowy z menu poniżej:**", view=AgeSelectView())
            await channel.send("**🚻 Wybierz swoją płeć z menu poniżej:**", view=GenderSelectView())
            mark_role_messages_sent()
            print("✅ Wysłano wiadomości z rolami.")
        except Exception as e:
            print(f"❌ Błąd przy wysyłaniu wiadomości z rolami: {e}")
    else:
        print("ℹ️ Wiadomości z rolami już zostały wysłane wcześniej.")
def has_sent_role_messages():
    return os.path.exists(ROLES_SENT_FILE)

def mark_role_messages_sent():
    with open(ROLES_SENT_FILE, "w") as f:
        f.write("sent")

async def send_role_messages(channel):
    messages_to_send = [
        {
            "content": "**🎯 Wybierz swój przedział wiekowy z menu poniżej:**",
            "view": AgeSelectView()
        },
        {
            "content": "**🚻 Wybierz swoją płeć z menu poniżej:**",
            "view": GenderSelectView()
        }
    ]

    messages = [msg async for msg in channel.history(limit=50)]
    for m in messages_to_send:
        already_sent = any(
            msg.author == bot.user and m["content"] in (msg.content or "")
            for msg in messages
        )
        if not already_sent:
            await channel.send(content=m["content"], view=m["view"])
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(CHANNEL_ID)
    role = discord.utils.get(member.guild.roles, name="Zieloni Towarzysze")
    if role:
        await member.add_roles(role)

    if channel:
        embed = Embed(title="🎉 Witamy na serwerze!", description=f"{member.mention}, cieszymy się, że dołączyłeś/aś do **{member.guild.name}**! 🎉", color=0xFFFF00)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="Cieszymy się, że jesteś z nami!")
        await channel.send(embed=embed)
@bot.command(name='restart')
@commands.is_owner()
async def restart_bot(ctx):
    await ctx.send("🔄 Restartuję bota...")

    with open("restart_flag.txt", "w") as f:
        f.write(str(ctx.channel.id))  # poprawne zapisanie ID kanału

    await bot.close()  # Render automatycznie odpala z powrotem

@bot.command(name='commands')
async def commands_command(ctx):
    embed = discord.Embed(title="📜 Lista dostępnych komend", description="Poniżej znajdziesz wszystkie dostępne komendy:", color=discord.Color.gold())
    embed.add_field(name="`!commands`", value="🧲 Wyświetla tę listę komend.", inline=False)
    embed.add_field(name="`!ban @user [powód]`[ADM]", value="🔨 Banuje użytkownika (wymaga uprawnień).", inline=False)
    embed.add_field(name="`!mute @user`[ADM]", value="🔇 Mutuje użytkownika na 15 minut (wymaga uprawnień).", inline=False)
    embed.add_field(name="`!clear [liczba]`[ADM]", value="✅ Czyści określoną liczbę wiadomości (domyślnie 25).", inline=False)
    embed.add_field(name="`!profil`", value="🧲 Pokazuje Twój profil: role, data dołączenia, ID.", inline=False)
    embed.add_field(name="`!avatar [@user]`", value="🖼️ Wyświetla avatar Twój lub oznaczonego użytkownika.", inline=False)
    embed.add_field(name="`!serverinfo`", value="ℹ️ Informacje o serwerze.", inline=False)
    embed.add_field(name="`!rank`", value="🏆 Sprawdź swój aktualny poziom i exp.", inline=False)
    embed.add_field(name="`!ranking`", value="🥇 Wyświetla TOP 10 użytkowników.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Brak powodu"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Użytkownik {member.mention} został zbanowany. Powód: {reason}")

@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    guild = ctx.guild
    mute_role = discord.utils.get(guild.roles, name="Muted")
    if not mute_role:
        mute_role = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)
    await member.add_roles(mute_role)
    await ctx.send(f"🔇 {member.mention} został wyciszony na 15 minut.")
    await asyncio.sleep(15 * 60)
    await member.remove_roles(mute_role)
    await ctx.send(f"🔊 {member.mention} został automatycznie odmutowany.")

@bot.command(name='8ball')
async def eight_ball(ctx, *, question):
    responses = ["Tak!", "Nie.", "Może...", "Zdecydowanie!", "Wątpię w to.", "Spróbuj ponownie."]
    await ctx.send(f"🎱 {random.choice(responses)}")

@bot.command(name="ship")
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    score = random.randint(0, 100)
    bar = "█" * (score // 10) + "░" * (10 - score // 10)
    await ctx.send(f"💖 Dopasowanie między {user1.mention} a {user2.mention}:\n`[{bar}] {score}%`")


@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 25):
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Usunięto {len(deleted)} wiadomości.", delete_after=5)

@bot.command(name='profil')
async def profile(ctx):
    member = ctx.author
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(title=f"📋 Profil: {member.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📆 Dołączył", value=member.joined_at.strftime('%d.%m.%Y'), inline=False)
    embed.add_field(name="🎭 Role", value=", ".join(roles) if roles else "Brak", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='serverinfo')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title="ℹ️ Informacje o serwerze", color=discord.Color.green())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="💼 Nazwa", value=guild.name, inline=False)
    embed.add_field(name="👥 Liczba członków", value=guild.member_count, inline=False)
    embed.add_field(name="📆 Utworzony", value=guild.created_at.strftime('%d.%m.%Y'), inline=False)
    await ctx.send(embed=embed)

@bot.command(name='avatar')
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Avatar użytkownika: {member.display_name}", color=discord.Color.purple())
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="rank")
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    async with bot.db.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM levels WHERE user_id = $1", user_id)
        if not user:
            await ctx.send("❌ Ten użytkownik nie ma jeszcze żadnego poziomu.")
            return
        exp = user["exp"]
        level = user["level"]
    embed = discord.Embed(title=f"🏆 Poziom użytkownika: {member.display_name}", color=discord.Color.orange())
    embed.add_field(name="📊 EXP", value=exp, inline=False)
    embed.add_field(name="🎯 Poziom", value=level, inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="ranking", aliases=["rankin"])
async def ranking(ctx):
    async with bot.db.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM levels ORDER BY exp DESC LIMIT 10")
    embed = discord.Embed(title="🥇 Ranking TOP 10", color=discord.Color.gold())
    for i, row in enumerate(rows, start=1):
        member = ctx.guild.get_member(int(row["user_id"]))
        name = member.display_name if member else f"<@{row['user_id']}>"
        embed.add_field(name=f"#{i} {name}", value=f"Poziom {row['level']} - {row['exp']} EXP", inline=False)
    await ctx.send(embed=embed)
@bot.command(name='roast')
async def roast(ctx, member: discord.Member):
    roasty = [
        f"{member.display_name}, twoje IQ ma ujemny balans na koncie.",
        f"{member.display_name}, nawet Windows 95 byłby szybszy od twojego myślenia.",
        f"{member.display_name}, gdyby głupota bolała, krzyczałbyś 24/7.",
        f"{member.display_name}, jesteś powodem, dla którego instrukcje obsługi istnieją."
    ]
    await ctx.send(random.choice(roasty))
@bot.command(name='insult')
async def insult(ctx):
    insults = [
        "Masz osobowość jak biały chleb – bez smaku.",
        "Jesteś jak chmura – kiedy znikasz, dzień staje się lepszy.",
        "Jesteś powodem, dla którego istnieją bramki antyspamowe.",
        "Twoje opinie są jak Windows Update – nikt ich nie chce, ale i tak się pojawiają."
    ]
    await ctx.send(random.choice(insults))
@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(title=f"ℹ️ Informacje o użytkowniku: {member.display_name}", color=discord.Color.teal())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📆 Dołączył", value=member.joined_at.strftime('%d.%m.%Y'), inline=False)
    embed.add_field(name="🎭 Role", value=", ".join(roles) if roles else "Brak", inline=False)
    await ctx.send(embed=embed)

    if not hasattr(bot, "db"):
        return
    user_id = str(message.author.id)
    async with bot.db.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM levels WHERE user_id = $1", user_id)
        if not user:
            await conn.execute("INSERT INTO levels (user_id, exp, level) VALUES ($1, 0, 0)", user_id)
            exp = 0
            level = 0
        else:
            exp = user["exp"]
            level = user["level"]
        exp += random.randint(5, 10)
        new_level = floor(sqrt(exp / 20))
        if new_level > level:
            await message.channel.send(f"🎉 {message.author.mention} awansował(a) na **poziom {new_level}**!")
        await conn.execute("UPDATE levels SET exp = $1, level = $2 WHERE user_id = $3", exp, new_level, user_id)
    await bot.process_commands(message)

keep_alive()
def has_sent_role_messages():
    if not os.path.exists(ROLES_STATE_FILE):
        return False
    with open(ROLES_STATE_FILE, "r") as f:
        data = json.load(f)
    return data.get("sent", False)

def mark_role_messages_sent():
    with open(ROLES_STATE_FILE, "w") as f:
        json.dump({"sent": True}, f)
bot.run(TOKEN)
