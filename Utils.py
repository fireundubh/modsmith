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
    'alchemy_material_subtype.xml': 'alchemy_material_subtype_id',
    'alchemy_material_type.xml': 'alchemy_material_type_id',
    'ammo.xml': 'item_id',
    'ammo_class.xml': 'ammo_class_id',
    'armor.xml': 'item_id',
    'armor2clothing_attachment.xml': 'item_id',
    'armor2clothing_preset.xml': 'armor_id',
    'armor_archetype.xml': 'armor_archetype_id',
    # 'armor_archetype2body_subpart': None,
    'armor_class2engine_surface.xml': 'armor_class_id',
    'armor_subtype.xml': 'armor_subtype_id',
    'armor_type.xml': 'armor_type_id',
    'attachment2clothing_preset.xml': 'attachment_base_id',
    'attachment_base.xml': 'attachment_base_id',
    'attachment_slot.xml': 'attachment_slot_id',
    'blood_zone.xml': 'blood_zone_id',
    'body_layer.xml': 'body_layer_id',
    # 'body_material2subpart.xml': None,
    'body_part.xml': 'body_part_id',
    'body_subpart.xml': 'body_subpart_id',
    'buff.xml': 'buff_id',
    'buff_class.xml': 'buff_class_id',
    'buff_lifetime.xml': 'buff_lifetime_id',
    'character_head_archetype.xml': 'character_head_archetype_id',
    'clothing.xml': 'clothing_id',
    'clothing_attachment.xml': 'clothing_attachment_id',
    'clothing_mesh_data.xml': 'mesh_file_path',
    'clothing_preset.xml': 'clothing_preset_id',
    'clothing_raycast.xml': 'material',
    'consumable_item.xml': 'item_id',
    'die.xml': 'item_id',
    'divisible_item.xml': 'item_id',
    'document.xml': 'item_id',
    'document_class.xml': 'document_class_id',
    'document_content.xml': 'text',
    'document_content_images.xml': 'image',
    'document_transcription_topic.xml': 'text_id',
    'document_ui_layout.xml': 'document_ui_layout_id',
    'document_required_skill.xml': 'item_id',
    'document_requirement.xml': 'item_id',
    'document_reward.xml': 'item_id',
    'document_reward_perk.xml': 'item_id',
    'equipment_part.xml': 'equipment_part_id',
    'equipment_slot.xml': 'equipment_slot_name',
    'equippable_item.xml': 'item_id',
    'food.xml': 'item_id',
    'food_subtype.xml': 'food_subtype_id',
    'food_type.xml': 'food_type_id',
    'helmet.xml': 'item_id',
    'herb.xml': 'item_id',
    'herb_element_type.xml': 'id',
    'inventory.xml': 'item_id',
    'inventory2inventory_preset.xml': 'inventory_preset_id',
    # 'inventory2item.xml': None,
    'inventory_preset.xml': 'inventory_preset_id',
    # 'inventory_preset2item.xml': None,
    'item.xml': 'item_id',
    'item_category.xml': 'item_category_id',
    'item_manipulation_type.xml': 'id',
    'item_phase.xml': 'model',
    'key.xml': 'item_id',
    'key_subtype.xml': 'key_subtype_id',
    'key_type.xml': 'key_type_id',
    'keyring.xml': 'item_id',
    'keyring_type.xml': 'keyring_type_id',
    'location.xml': 'location_id',
    'location2perk.xml': 'perk_id',
    'melee_weapon.xml': 'item_id',
    'melee_weapon_type.xml': 'melee_weapon_type_id',
    'misc.xml': 'item_id',
    'misc_subtype.xml': 'misc_subtype_id',
    'misc_type.xml': 'misc_type_id',
    'missile_weapon.xml': 'item_id',
    'missile_weapon_class2ammo_class.xml': 'missile_weapon_class_id',
    'missile_weapon_type.xml': 'missile_weapon_type_id',
    'npc_tool.xml': 'item_id',
    'npc_tool_subtype.xml': 'npc_tool_subtype_id',
    'npc_tool_type.xml': 'npc_tool_type_id',
    'ointment_item.xml': 'item_id',
    'ointment_item_subtype.xml': 'ointment_item_subtype_id',
    'ointment_item_type.xml': 'ointment_item_type_id',
    'pickable_area_desc.xml': 'id',
    'pickable_area_material.xml': 'material_name',
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
    'pickable_item.xml': 'item_id',
    'player_item.xml': 'item_id',
    'potion.xml': 'item_id',
    'questible_item.xml': 'item_id',
    'recipe.xml': 'recipe_id',
    'recipe_ingredient.xml': 'item_id',
    'recipe_step.xml': 'ui_text',
    # 'recipe_substep.xml': None,
    'rpg_param.xml': 'rpg_param_key',
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
    'weapon_class.xml': 'weapon_class_id',
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
    def write_output_xml(xml_data, file_path, i18n=False):
        if i18n:
            with open(file_path, 'w', encoding='utf8') as f:
                f.write(etree.tostring(xml_data, pretty_print=True).decode('unicode-escape'))
        else:
            et = etree.ElementTree(xml_data)
            et.write(file_path, encoding='us-ascii', xml_declaration=True, pretty_print=True)
