import os
import discord
from discord import ui, app_commands
from discord.ext import commands

# Вставьте сюда токен вашего бота
TOKEN = os.getenv("API_TOKEN") or os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: Не найден токен бота в переменных окружения (API_TOKEN или DISCORD_TOKEN).")
    exit(1)
GUILD_ID = 1443435567432994857 # ID вашего сервера
ADMIN_CHANNEL_ID = 1444938279232208999 # ID канала, куда падают заявки

# Настройка интентов (прав)
intents = discord.Intents.default()
intents.members = True # Важно для смены ников и выдачи ролей
intents.message_content = True

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Бот {self.user} запущен!')
        try:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        except Exception as e:
            print(e)

client = Client(command_prefix="!", intents=intents)

# --- 1. Модальное окно для ввода ФИО ---
class RegisterModal(ui.Modal, title="Регистрация в колледже"):
    fio = ui.TextInput(
        label="Ваше ФИО (Полностью)",
        style=discord.TextStyle.short,
        placeholder="Иванов Иван Иванович",
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Сохраняем ФИО во временное хранилище (или передаем дальше)
        # Переходим к выбору роли
        view = RoleSelectView(self.fio.value)
        await interaction.response.send_message(
            f"Спасибо, {self.fio.value}. Теперь выберите вашу роль:", 
            view=view, 
            ephemeral=True
        )

# --- 2. Выбор роли и группы ---
class RoleSelectView(ui.View):
    def __init__(self, fio_value):
        super().__init__()
        self.fio = fio_value
        self.selected_role = None
        self.selected_group = None

    @discord.ui.select(
        placeholder="Выберите статус...",
        options=[
            discord.SelectOption(label="Студент", emoji="🎓", value="student"),
            discord.SelectOption(label="Преподаватель", emoji="📚", value="teacher"),
        ]
    )
    async def select_role(self, interaction: discord.Interaction, select: ui.Select):
        self.selected_role = select.values[0]
        
        if self.selected_role == "teacher":
            # Преподавателям группа не нужна, сразу отправляем на проверку
            await self.send_to_admin(interaction)
        else:
            # Студентам показываем выбор группы (обновляем сообщение)
            # Примечание: В реальном боте лучше использовать отдельный Select, который появляется динамически
            # Здесь упрощенный пример:
            self.clear_items() # Убираем выбор роли
            self.add_item(GroupSelect(self.fio, self.selected_role)) # Добавляем выбор группы
            await interaction.response.edit_message(content="Выберите вашу учебную группу:", view=self)

    async def send_to_admin(self, interaction: discord.Interaction):
        # Логика отправки администраторам (см. ниже)
        pass 

class GroupSelect(ui.Select):
    def __init__(self, fio, role):
        # Список групп. В реальности их можно брать из базы данных
        options = [
            # ТИС (Технология информационных систем)
            discord.SelectOption(label="ТИС - Группа 5", value="group_5_TIS"),
            discord.SelectOption(label="ТИС - Группа 6", value="group_6_TIS"),
            discord.SelectOption(label="ТИС - Группа 7", value="group_7_TIS"),
            discord.SelectOption(label="ТИС - Группа 8", value="group_8_TIS"),
            discord.SelectOption(label="ТИС - Группа 9", value="group_9_TIS"),
            discord.SelectOption(label="ТИС - Группа 10", value="group_10_TIS"),
            discord.SelectOption(label="ТИС - Группа 11", value="group_11_TIS"),
            discord.SelectOption(label="ТИС - Группа 12", value="group_12_TIS"),
            discord.SelectOption(label="ТИС - Группа 13", value="group_13_TIS"),
            discord.SelectOption(label="ТИС - Группа 14", value="group_14_TIS"),
            discord.SelectOption(label="ТИС - Группа 15", value="group_15_TIS"),
            discord.SelectOption(label="ТИС - Группа 23", value="group_23_TIS"),
            
            # РПО (Разработка программного обеспечения)
            discord.SelectOption(label="РПО - Группа 16", value="group_16_RPO"),
            discord.SelectOption(label="РПО - Группа 18", value="group_18_RPO"),
            discord.SelectOption(label="РПО - Группа 19", value="group_19_RPO"),
            discord.SelectOption(label="РПО - Группа 20", value="group_20_RPO"),
            discord.SelectOption(label="РПО - Группа 22", value="group_22_RPO"),
            
            # МАР (Мобильные и арт-системы)
            discord.SelectOption(label="МАР - Группа 24", value="group_24_MAR"),
            
            # ВД (Вождение)
            discord.SelectOption(label="ВД - Группа 21", value="group_21_VD"),
        ]
        super().__init__(placeholder="Выберите группу", options=options)
        self.fio = fio
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        # Отправка заявки админам
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        
        # Создаем Embed для админов
        embed = discord.Embed(title="🔔 Новая заявка на регистрацию", color=discord.Color.yellow())
        embed.add_field(name="Пользователь", value=interaction.user.mention, inline=False)
        embed.add_field(name="Указанное ФИО", value=self.fio, inline=False)
        embed.add_field(name="Роль", value="Студент", inline=True)
        embed.add_field(name="Группа", value=self.values[0], inline=True)
        
        # Кнопки принятия решения
        view = AdminApproveView(
            user_id=interaction.user.id, 
            fio=self.fio, 
            role_type="student", 
            group_value=self.values[0]
        )
        
        await admin_channel.send(embed=embed, view=view)
        await interaction.response.edit_message(content="✅ Заявка отправлена модераторам! Ожидайте подтверждения.", view=None)

# --- 3. Панель Администратора (Принять/Отклонить) ---
class AdminApproveView(ui.View):
    def __init__(self, user_id, fio, role_type, group_value=None):
        super().__init__(timeout=None) # Кнопки вечные
        self.user_id = user_id
        self.fio = fio
        self.role_type = role_type
        self.group_value = group_value

    @discord.ui.button(label="Одобрить", style=discord.ButtonStyle.green, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        if not member:
            await interaction.response.send_message("Пользователь вышел с сервера.", ephemeral=True)
            return

        try:
            # 1. Смена ника
            await member.edit(nick=self.fio)
            
            # 2. Выдача ролей (Нужно заранее создать роли с такими именами или ID)
            roles_to_add = []
            
            # Основная роль доступа (например, "Верифицирован")
            verified_role = discord.utils.get(guild.roles, name="Верифицирован")
            if verified_role: roles_to_add.append(verified_role)

            # Роль группы
            if self.group_value:
                # Маппинг значений групп на названия ролей
                group_mapping = {
                    "group_5_TIS": "5 ТИС / 23",
                    "group_6_TIS": "6 ТИС / 23",
                    "group_7_TIS": "7 ТИС / 23",
                    "group_8_TIS": "8 ТИС / 23",
                    "group_9_TIS": "9 ТИС / 24",
                    "group_10_TIS": "10 ТИС / 24",
                    "group_11_TIS": "11 ТИС / 24",
                    "group_12_TIS": "12 ТИС / 24",
                    "group_13_TIS": "13 ТИС / 24",
                    "group_14_TIS": "14 ТИС / 24",
                    "group_15_TIS": "15 ТИС / 24",
                    "group_23_TIS": "23 ТИС / 25",
                    "group_16_RPO": "16 РПО / 25",
                    "group_18_RPO": "18 РПО / 25",
                    "group_19_RPO": "19 РПО / 25",
                    "group_20_RPO": "20 РПО / 25",
                    "group_22_RPO": "22 РПО / 25",
                    "group_24_MAR": "24 МАР / 25",
                    "group_21_VD": "21 ВД / 25",
                }
                
                group_role_name = group_mapping.get(self.group_value)
                if group_role_name:
                    group_role = discord.utils.get(guild.roles, name=group_role_name)
                    if group_role:
                        roles_to_add.append(group_role)

            if roles_to_add:
                await member.add_roles(*roles_to_add)

            # Обновляем сообщение админа
            await interaction.message.edit(content=f"✅ Заявка одобрена администратором {interaction.user.mention}", view=None, embed=None)
            
            # Пишем пользователю в ЛС (опционально)
            try:
                await member.send(f"Ваша заявка одобрена! Добро пожаловать, {self.fio}.")
            except:
                pass

        except discord.Forbidden:
            await interaction.response.send_message("❌ Ошибка прав! У бота роль ниже, чем та, которую он пытается выдать, или он не может менять ники.", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="⛔")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send("Ваша заявка на регистрацию отклонена администрацией. Проверьте данные и попробуйте снова.")
            except:
                pass
        await interaction.message.edit(content=f"⛔ Заявка отклонена администратором {interaction.user.mention}", view=None, embed=None)

# --- 4. Команда запуска ---
@client.tree.command(name="setup_reg", description="Создать сообщение регистрации")
@app_commands.checks.has_permissions(administrator=True)
async def setup_reg(interaction: discord.Interaction):
    view = ui.View()
    # Кнопка, открывающая модальное окно
    btn = ui.Button(label="Пройти регистрацию", style=discord.ButtonStyle.primary, emoji="📝")
    
    async def btn_callback(inter):
        await inter.response.send_modal(RegisterModal())
    
    btn.callback = btn_callback
    view.add_item(btn)
    
    await interaction.channel.send(
        "**Добро пожаловать на сервер Колледжа!**\n\nДля получения доступа к каналам, пожалуйста, нажмите кнопку ниже, укажите ФИО и выберите группу.", 
        view=view
    )
    await interaction.response.send_message("Меню создано!", ephemeral=True)

client.run(TOKEN)