import discord
import config
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from typing import Optional, List
from setup.GameInit import GameInit
from helpers.GamestateHelper import GamestateHelper
from helpers.DrawHelper import DrawHelper
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import random


class TileCommands(commands.GroupCog, name="tile"):
    def __init__(self, bot):
        self.bot = bot

    color_choices = [
        app_commands.Choice(name="Blue", value="blue"),
        app_commands.Choice(name="Red", value="red"),
        app_commands.Choice(name="Yellow", value="yellow"),
        app_commands.Choice(name="Purple", value="purple"),
        app_commands.Choice(name="Green", value="green"),
        app_commands.Choice(name="White", value="white")
    ]

    @app_commands.command(name="manage_units", description="add or remove units from a tile")
    @app_commands.choices(color=color_choices)
    async def manage_units(self, interaction: discord.Interaction, tile_position: str,
                        interceptors: Optional[int],
                        cruisers: Optional[int],
                        dreadnoughts: Optional[int],
                        starbase: Optional[int],
                        influence: Optional[bool],
                        color: Optional[app_commands.Choice[str]]=None):
        """

        :param interceptors: Use +1/-1 to add/subtract interceptors
        :param cruisers: Use +1/-1 to add/subtract cruisers
        :param dreadnoughts: Use +1/-1 to add/subtract dreadnoughts
        :param starbase: Use +1/-1 to add/subtract starbases
        :param influence: Use True/False to add or remove your influence disc from this tile
        :param color: Choose player color. Default is your own color
        :return:
        """
        game = GamestateHelper(interaction.channel)  
        player_color = color.value if color else game.get_player(str(interaction.user.id))["color"]  
        
        added_units, removed_units = [], []  
        
        def process_units(unit_type, count):  
            unit_code = f"{player_color}-{unit_type}"  
            if count:  
                units_list = added_units if count > 0 else removed_units  
                for x in range(abs(count)):  
                    units_list.append(unit_code)  

        process_units("int", interceptors)  
        process_units("cru", cruisers)  
        process_units("drd", dreadnoughts)  
        process_units("sb", starbase)  

        if added_units:  
            game.add_units(added_units, tile_position)  
        if removed_units:  
            game.remove_units(removed_units, tile_position)  
        
        if influence != None:
            if influence:
                if game.gamestate["board"][tile_position]["owner"] != 0:
                    game.remove_control(game.gamestate["board"][tile_position]["owner"], tile_position)
                game.add_control(player_color, tile_position)
            else:
                game.remove_control(player_color, tile_position)

        await interaction.response.defer(thinking=True)  
        drawing = DrawHelper(game.gamestate)  
        image = drawing.board_tile_image(tile_position)  
        await interaction.followup.send(file=drawing.show_single_tile(image)) 



    @app_commands.command(name="manage_population", description="add or remove population cubes (using positive or negative numbers) from a tile")
    @app_commands.choices(color=color_choices)
    async def manage_population(self, interaction: discord.Interaction, tile_position: str,
                        money: Optional[int],
                        science: Optional[int],
                        material: Optional[int],
                        neutral: Optional[int],
                        advanced_money: Optional[int],
                        advanced_science: Optional[int],
                        advanced_material: Optional[int],
                        advanced_neutral: Optional[int],
                        influence: Optional[bool],
                        color: Optional[app_commands.Choice[str]]=None):
        """
        :param influence: Use True/False to add or remove your influence disc from this tile
        :param color: Choose player color. Default is your own color
        :return:
        """
        game = GamestateHelper(interaction.channel)  
        player_color = color.value if color else game.get_player(str(interaction.user.id))["color"]  
        playerID = game.get_player_from_color(player_color)
        added_pop, removed_pop = [], []  
        
        def process_pop(pop_type, count):  
            pop_code = f"{pop_type}_{"pop"}"  
            if count:  
                pop_list = added_pop if count > 0 else removed_pop  
                for x in range(abs(count)):  
                    pop_list.append(pop_code)  

        process_pop("money", money)  
        process_pop("science", science)  
        process_pop("neutral", neutral)  
        process_pop("material", material)
        process_pop("moneyadv", advanced_money)  
        process_pop("scienceadv", advanced_science)  
        process_pop("neutraladv", advanced_neutral)  
        process_pop("materialadv", advanced_material)    

        if added_pop:  
            game.add_pop(added_pop, tile_position,playerID)  
        if removed_pop:  
            game.remove_pop(removed_pop, tile_position,playerID)  

        if influence != None:
            if influence:
                if game.gamestate["board"][tile_position]["owner"] != 0:
                    game.remove_control(game.gamestate["board"][tile_position]["owner"], tile_position)
                game.add_control(player_color, tile_position)
            else:
                game.remove_control(player_color, tile_position)

        await interaction.response.defer(thinking=True)  
        drawing = DrawHelper(game.gamestate)  
        image = drawing.board_tile_image(tile_position)  
        await interaction.followup.send(file=drawing.show_single_tile(image)) 

    @app_commands.command(name="add_influence")
    @app_commands.choices(color=color_choices)
    async def add_influence(self, interaction: discord.Interaction, tile_position: str, color: app_commands.Choice[
        str]):
        game = GamestateHelper(interaction.channel)
        if game.gamestate["board"][tile_position]["owner"] != 0:
            await interaction.response.send_message("Please remove the current influence disc first")
            return
        game.add_control(color.value, tile_position)
        await interaction.response.defer(thinking=True)
        drawing = DrawHelper(game.gamestate)
        image = drawing.board_tile_image(tile_position)
        await interaction.followup.send(file=drawing.show_single_tile(image))
    @app_commands.command(name="remove_influence")
    @app_commands.choices(color=color_choices)
    async def remove_influence(self, interaction: discord.Interaction, tile_position: str, color: app_commands.Choice[
        str]):
        game = GamestateHelper(interaction.channel)
        if game.gamestate["board"][tile_position]["owner"] == 0:
            await interaction.response.send_message("This tile already has no influence.")
            return
        game.remove_control(color.value, tile_position)
        await interaction.response.defer(thinking=True)
        drawing = DrawHelper(game.gamestate)
        image = drawing.board_tile_image(tile_position)
        await interaction.followup.send(file=drawing.show_single_tile(image))

    @app_commands.command(name="explore")
    async def explore(self, interaction: discord.Interaction, tile_position: str):
        game = GamestateHelper(interaction.channel)
        tile = game.tile_draw(tile_position)
        drawing = DrawHelper(game.gamestate)
        await interaction.response.defer(thinking=True)
        image = drawing.base_tile_image(tile)
        await interaction.followup.send(file=drawing.show_single_tile(image))
        view = View()
        button = Button(label="Place Tile",style=discord.ButtonStyle.success, custom_id=f"place_tile_{tile_position}_{tile}")
        button2 = Button(label="Discard Tile",style=discord.ButtonStyle.danger, custom_id=f"discard_tile_{tile}")
        view.add_item(button)
        view.add_item(button2)
        await interaction.channel.send(view=view)

    @app_commands.command(name="show_tile")
    async def show_tile(self, interaction: discord.Interaction, tile_position: str):
        game = GamestateHelper(interaction.channel)
        await interaction.response.defer(thinking=True)
        drawing = DrawHelper(game.gamestate)
        try:
            image = drawing.board_tile_image(tile_position)
            await interaction.followup.send(file=drawing.show_single_tile(image))
        except KeyError:
            await interaction.followup.send("This tile does not exist!")

    @app_commands.command(name="show_base_tile")
    async def show_base_tile(self, interaction: discord.Interaction, sector: str):
        game = GamestateHelper(interaction.channel)
        await interaction.response.defer(thinking=True)
        drawing = DrawHelper(game.gamestate)
        try:
            image = drawing.base_tile_image(sector)
            await interaction.followup.send(file=drawing.show_single_tile(image))
        except ValueError:
            await interaction.followup.send("This tile does not exist!")

    @app_commands.command(name="show_game")
    async def show_game(self, interaction: discord.Interaction):
        game = GamestateHelper(interaction.channel)
        await interaction.response.defer(thinking=True)
        drawing = DrawHelper(game.gamestate)
        await interaction.followup.send(file=drawing.show_game())
        view = View()
        button = Button(label="Show Game",style=discord.ButtonStyle.primary, custom_id="showGame")
        view.add_item(button)
        await interaction.channel.send(view=view)