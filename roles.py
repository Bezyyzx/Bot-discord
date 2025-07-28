import os
import json
import discord
from discord.ui import Select, View

ROLE_MESSAGE_FILE = "role_message_ids.json"

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

class AgeSelectView(View):
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

# Zapisywanie i wczytywanie ID wiadomości
def save_role_message_ids(age_msg_id, gender_msg_id):
    with open(ROLE_MESSAGE_FILE, "w") as f:
        json.dump({"age": age_msg_id, "gender": gender_msg_id}, f)

def load_role_message_ids():
    if not os.path.exists(ROLE_MESSAGE_FILE):
        return None, None
    with open(ROLE_MESSAGE_FILE, "r") as f:
        data = json.load(f)
        return data.get("age"), data.get("gender")

def has_sent_role_messages():
    return os.path.exists(ROLE_MESSAGE_FILE)

def mark_role_messages_sent():
    # Prosta wersja – możesz ją rozszerzyć jeśli chcesz coś więcej zapisać
    if not os.path.exists(ROLE_MESSAGE_FILE):
        with open(ROLE_MESSAGE_FILE, "w") as f:
            json.dump({"sent": True}, f)
