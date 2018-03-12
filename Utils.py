# coding=utf-8

import os
import re

from lxml import etree

DATA_MAP = {
    'Data\Libs\Tables': 'Tables.pak',
    'Data\Scripts': 'Scripts.pak',
    'Data\Libs': 'Scripts.pak',
    'Data\Entities': 'Scripts.pak'
}

KEY_MAP = {
    'achievement.xml': 'achievement_id',
    'achievement_rule.xml': 'achievement_id',
    'alchemy_base.xml': 'item_id',
    'alchemy_material.xml': 'item_id',
    'ammo.xml': 'item_id',
    'armor.xml': 'item_id',
    'armor2clothing_attachment.xml': 'item_id',
    'armor2clothing_preset.xml': 'armor_id',
    'attachment_base_id': 'attachment_base_id',
    'buff.xml': 'buff_id',
    'buff_class.xml': 'buff_class_id',
    'buff_lifetime.xml': 'buff_lifetime_id',
    'consumable_item': 'item_id',
    'die.xml': 'item_id',
    'divisible_item.xml': 'item_id',
    'document.xml': 'item_id',
    'document_required_skill.xml': 'item_id',
    'document_requirement.xml': 'item_id',
    'document_reward.xml': 'item_id',
    'document_reward_perk.xml': 'item_id',
    'equippable_item.xml': 'item_id',
    'food.xml': 'item_id',
    'helmet.xml': 'item_id',
    'herb.xml': 'item_id',
    # 'inventory.xml': 'item_id',
    # 'inventory2inventory_preset.xml': 'inventory_preset_id',
    # 'inventory_preset.xml': 'inventory_preset_id',
    'item.xml': 'item_id',
    'item_phase.xml': 'item_id',
    'key.xml': 'item_id',
    'keyring.xml': 'item_id',
    'location.xml': 'location_id',
    'location2perk.xml': 'perk_id',
    'melee_weapon.xml': 'item_id',
    'misc.xml': 'item_id',
    'missile_weapon.xml': 'item_id',
    'npc_tool.xml': 'item_id',
    'ointment_item.xml': 'item_id',
    'perk.xml': 'perk_id',
    'perk_buff.xml': 'buff_id',
    'perk_buff_override.xml': 'perk_id',
    'perk_codex.xml': 'perk_id',
    'perk_combo_step.xml': 'perk_id',
    'perk_companion.xml': 'perk_id',
    'perk_recipe.xml': 'perk_id',
    'perk_script.xml': 'perk_id',
    'perk_soul_ability.xml': 'perk_id',
    'perk_special_riposte.xml': 'perk_id',
    'perk2perk_exclusivity.xml': 'first_perk_id',
    'pickable_area_desc.xml': 'guid_item_picked',
    'pickable_item.xml': 'item_id',
    'player_item.xml': 'item_id',
    'potion.xml': 'item_id',
    'questible_item.xml': 'item_id',
    # 'recipe.xml': 'recipe_id',
    # 'recipe_ingredient': 'item_id',
    'skill.xml': 'skill_id',
    'skill2item_category.xml': 'skill_id',
    'soul.xml': 'soul_id',
    'soul2hobby.xml': 'soul_id',
    'soul2inventory.xml': 'soul_id',
    'soul2metarole.xml': 'soul_id',
    'soul2perk.xml': 'soul_id',
    'soul2role.xml': 'soul_id',
    'soul2skill.xml': 'soul_id',
    'soul_slot2health.xml': 'soul_id',
    'soul_slot2weapon_health.xml': 'soul_id',
    'v_soul2role_metarole.xml': 'soul_id',
    'v_soul_character_data.xml': 'soul_id',
    'soul_archetype.xml': 'soul_archetype_id',
    'soul_archetype_movement.xml': 'soul_archetype_id',
    'weapon.xml': 'item_id',
    'weapon2weapon_preset.xml': 'item_id',
    'weapon_attachment_slot.xml': 'weapon_attachment_slot_id',
    'weapon_equip_slot.xml': 'weapon_equip_slot_id',
    'weapon_preset.xml': 'weapon_preset_id',
    'weapon_sub_class.xml': 'weapon_sub_class_id'
}


class Utils:
    @staticmethod
    def strip_whitespace(text):
        if text:
            text = re.sub('\s+', ' ', text)
            return text.strip()

    @staticmethod
    def get_key_by_filename(filename):
        for key in KEY_MAP.keys():
            if key == filename:
                return KEY_MAP[key]

    @staticmethod
    def get_pak_by_path(xml_path):
        for key in DATA_MAP.keys():
            if key in xml_path:
                return DATA_MAP[key]

    @staticmethod
    def setup_xml_files(path, files):
        return [os.path.split(f.replace(path + '\\', '')) for f in files]

    @staticmethod
    def setup_xml_data(path, file):
        xml_path = os.path.join(path, *file)
        xml = etree.parse(xml_path, etree.XMLParser(remove_blank_text=True)).getroot()
        rows = xml.findall('table/rows/row') or xml.findall('Row')
        return {'xml_path': xml_path, 'xml_rows': rows}

    @staticmethod
    def write_output_xml(xml_data, file_path):
        with open(file_path, 'w', encoding='utf8') as f:
            f.write(etree.tostring(xml_data, pretty_print=True).decode('unicode-escape'))
