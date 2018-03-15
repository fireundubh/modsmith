# coding=utf-8

import os
import re

from lxml import etree

DATA_MAP = {
    'Data\Scripts': 'Scripts.pak',
    'Data\Libs\Tables': 'Tables.pak',
    'Data\Libs': 'Scripts.pak',
    'Data\Entities': 'Scripts.pak',
}

SIGNATURES = {
    # Data/Libs/Tables
    # -------------------------------------------------------------------------
    'character_beard': 'character_beard_id',
    'character_body': 'character_body_id',
    'character_hair': 'character_hair_id',
    'character_head': 'character_head_id',
    'editor_object': 'id',
    'editor_object_binding': ['source_id', 'target_id'],
    'hdr_preset': 'name',
    'random_event': 'random_event_id',
    'random_event_option': 'random_event_option_id',
    'random_event_option_set': 'random_event_option_set_id',
    'random_event_source_type': 'random_event_source_type_id',

    # Data/Libs/Tables/action
    # -------------------------------------------------------------------------
    'actor_action_fragment_id_mapping': 'actor_action_fragment_id_mapping_id',
    'actor_action_standup': 'animation_id',
    'actor_action_transition_to_combat': ['actor_action_type_id', 'actor_action_type_id_request', 'actor_activity_id', 'actor_pose_id', 'mn_fragment_id', 'mn_tags'],
    'actor_action_type': 'actor_action_type_id',
    'actor_action_type_group': ['actor_action_type_group_id', 'actor_action_type_id'],
    'actor_activity': 'actor_activity_id',
    'actor_pose': 'actor_pose_id',
    'actor_tag_mapping': 'mn_tag',

    # Data/Libs/Tables/ai
    # -------------------------------------------------------------------------
    # 'ai_body': '',
    # 'ai_body2brain_sensor': '',
    # 'ai_body2npc_reference_point': '',
    # 'ai_percept_handler': '',
    # 'ai_percept_handler_type': '',
    # 'ai_variable_form': '',
    # 'ai_variable_sync': '',
    # 'brain': '',
    # 'brain2brain_interpreter': '',
    # 'brain2mailbox': '',
    # 'brain2subbrain': '',
    # 'brain_interpreter': '',
    # 'brain_interpreter2brain_message_type': '',
    # 'brain_interpreter_type': '',
    # 'brain_message_type': '',
    # 'brain_sensor': '',
    # 'brain_sensor_type': '',
    # 'brain_variable': '',
    # 'mailbox': '',
    # 'mailbox_action_type': '',
    # 'mailbox_filter': '',
    # 'mailbox_filter_action': '',
    # 'mailbox_group': '',
    # 'mailbox_group2mailbox': '',
    # 'mailbox_rule': '',
    # 'npc_reference_point': '',
    # 'positioning_shape': '',
    # 'positioning_vertex': '',
    # 'sa_behaviour_action': '',
    # 'sa_behaviour_tag': '',
    # 'sa_behaviour_tag2mailbox': '',
    # 'sa_behaviour_tag_parent': '',
    # 'sa_smart_area': '',
    # 'sa_smart_area2sa_behaviour_tag': '',
    # 'se_condition_type': '',
    # 'situation': '',
    # 'situation_frequency': '',
    # 'situation_global_condition': '',
    # 'situation_role': '',
    # 'situation_role2mailbox': '',
    # 'situation_role_condition': '',
    # 'situation_role_tree': '',
    # 'situation_variant': '',
    # 'so_behaviour_action': '',
    # 'so_behaviour_state': '',
    # 'so_behaviour_tag': '',
    # 'so_behaviour_tag2mailbox': '',
    # 'so_behaviour_tag_condition': '',
    # 'so_behaviour_tag_navigation': '',
    # 'so_behaviour_tag_parent': '',
    # 'so_item_smart_object': '',
    # 'so_smart_object': '',
    # 'so_smart_object2so_behaviour_tag': '',
    # 'subbrain': '',
    # 'subbrain2ai_percept_handler': '',
    # 'subbrain_behaviour_tree': '',
    # 'subbrain_combat': '',
    # 'subbrain_dialog': '',
    # 'subbrain_situation': '',
    # 'subbrain_smart_area': '',
    # 'subbrain_smart_object': '',
    # 'subbrain_switching': '',
    # 'subbrain_type': '',

    # Data/Libs/Tables/animation
    # -------------------------------------------------------------------------
    'ai_fragment_exclude': 'ai_fragment_exclude_id',
    'anim_fragment': ['actor_class_hash', 'mn_fragment_id', 'mn_tags'],
    'anim_fragment_do_not_interrupt': ['actor_class_hash', 'mn_fragment_id', 'mn_tags'],
    'anim_fragment_events': ['abs_event_time', 'event_name', 'actor_class_hash', 'mn_fragment_id', 'mn_option_index', 'mn_tags'],
    'hit_reaction': ['actor_class_hash', 'hit_reaction_type_id', 'mn_fragment_id_str', 'mn_tag_state_str', 'mn_option_index'],
    'hit_reaction_type': 'hit_reaction_type_id',
    'jump': ['actor_class_hash', 'mn_fragment_id', 'mn_tags'],
    'ladder': ['actor_class_hash', 'mn_fragment_id', 'mn_tags'],
    'mn_fragment': 'mn_fragment_id',
    'picking': ['actor_class_hash', 'mn_frag_tag_state'],

    # Data/Libs/Tables/combat
    # -------------------------------------------------------------------------
    'combat_action_attack': 'mn_tags',
    'combat_action_block': 'blk_mn_tags',
    'combat_action_block_movement': 'mn_tags',
    'combat_action_failed_attack': 'mn_tags',
    'combat_action_fragment_id_mapping': 'combat_action_fragment_id_mapping_id',
    'combat_action_guard_movement': 'mn_tags',
    'combat_action_guard_sync_movement': 'mn_tags',
    'combat_action_hit': 'hit_mn_tags',
    'combat_action_hit_movement': 'mn_tags',
    'combat_action_perfect_block': 'blk_mn_tags',
    'combat_action_pose_modifier': 'mn_tags',
    'combat_action_sync_attack': 'mn_tags',
    'combat_action_sync_hit': 'mn_tags',
    'combat_action_sync_pb_hit': 'mn_tags',
    'combat_action_sync_transition': 'mn_tags',
    'combat_action_text': 'string_name',
    'combat_action_trigger': 'combat_action_trigger_id',
    'combat_action_type': 'combat_action_type_id',
    'combat_action_type_group': ['combat_action_type_group_id', 'combat_action_type_id'],
    'combat_action_type_mapping': ['dst_action_type_id', 'src_action_type_id'],
    'combat_attack_config': 'combat_attack_config_id',
    'combat_attack_hit_statistics': ['body_subpart_id', 'hit_count'],
    'combat_attack_type': 'combat_attack_type_id',
    'combat_attack_type_tag': ['combat_attack_type_id', 'combat_tag_id'],
    'combat_combo': 'combat_combo_id',
    'combat_combo_step': ['combat_combo_id', 'step'],
    'combat_damage_type_mapping': ['combat_attack_type_id', 'r_weapon_class_id', 'r_weapon_sub_class_id', 'rpg_damage_type_id'],
    'combat_guard_stance': 'combat_guard_stance_id',
    'combat_guard_type': 'combat_guard_type_id',
    'combat_hit_origin': 'combat_hit_origin_id',
    'combat_hit_type': 'combat_hit_type_id',
    'combat_input_class': 'combat_input_class_id',
    'combat_native_guard_zone': ['combat_guard_stance_id', 'combat_zone_id', 'l_weapon_class_id', 'r_weapon_class_id'],
    'combat_native_guard_zones': ['combat_guard_stance_id', 'combat_zone_id'],
    'combat_riposte_chain': 'combat_riposte_chain_strid',
    'combat_riposte_chain_step': ['combat_riposte_chain_id', 'step'],
    'combat_side': 'combat_side_id',
    'combat_sync_action_hit': 'mn_fragment_id',
    'combat_tag': 'combat_tag_id',
    'combat_ui_rules': 'combat_ui_rules_id',
    'combat_weapon_group': 'combat_weapon_group_id',
    'combat_weapon_group_to_class': ['combat_weapon_group_id', 'weapon_class_id'],
    'combat_zone': 'combat_zone_id',
    'combat_zone_config': 'combat_zone_config_id',
    'combat_zone_distance': ['src_combat_zone_id', 'dst_combat_zone_id'],
    'combat_zone_mapping': ['src_zone_id', 'dst_zone_id', 'weapon_class_id', 'combat_input_class_id', 'combat_attack_type_id', 'combat_action_type_id'],
    'combat_zone_tag': 'combat_zone_id',

    # Data/Libs/Tables/DBEntity
    # -------------------------------------------------------------------------
    'entity_link': ['entity_id', 'target_id'],
    'stash': 'stash_id',

    # Data/Libs/Tables/inventory
    # -------------------------------------------------------------------------
    'inventory': 'item_id',
    'inventory2inventory_preset': 'inventory_preset_id',
    'inventory2item': ['inventory_id', 'item_id'],
    'inventory_preset': 'inventory_preset_id',
    'inventory_preset2item': ['inventory_preset_id', 'item_id'],

    # Data/Libs/Tables/item
    # -------------------------------------------------------------------------
    'alchemy_base': 'item_id',
    'alchemy_material': 'item_id',
    'alchemy_material_subtype': 'alchemy_material_subtype_id',
    'alchemy_material_type': 'alchemy_material_type_id',
    'ammo': 'item_id',
    'ammo_class': 'ammo_class_id',
    'armor': 'item_id',
    'armor2clothing_attachment': 'item_id',
    'armor2clothing_preset': 'armor_id',
    'armor_archetype': 'armor_archetype_id',
    'armor_archetype2body_subpart': ['armor_archetype_id', 'body_subpart_id'],
    'armor_class2engine_surface': 'armor_class_id',
    'armor_subtype': 'armor_subtype_id',
    'armor_type': 'armor_type_id',
    'attachment2clothing_preset': 'attachment_base_id',
    'attachment_base': 'attachment_base_id',
    'attachment_slot': 'attachment_slot_id',
    'blood_zone': 'blood_zone_id',
    'body_layer': 'body_layer_id',
    'body_material2subpart': ['race_id', 'body_material_name', 'body_subpart_id'],
    'body_part': 'body_part_id',
    'body_subpart': 'body_subpart_id',
    'character_head_archetype': 'character_head_archetype_id',
    'clothing': 'clothing_id',
    'clothing_attachment': 'clothing_attachment_id',
    'clothing_mesh_data': 'mesh_file_path',
    'clothing_preset': 'clothing_preset_id',
    'clothing_raycast': 'material',
    'consumable_item': 'item_id',
    'die': 'item_id',
    'divisible_item': 'item_id',
    'document': 'item_id',
    'document_class': 'document_class_id',
    'document_content': 'text',
    'document_content_images': 'image',
    'document_transcription_topic': 'text_id',
    'document_ui_layout': 'document_ui_layout_id',
    'equipment_part': 'equipment_part_id',
    'equipment_slot': 'equipment_slot_name',
    'equippable_item': 'item_id',
    'food': 'item_id',
    'food_subtype': 'food_subtype_id',
    'food_type': 'food_type_id',
    'helmet': 'item_id',
    'herb': 'item_id',
    'herb_element_type': 'id',
    'item': 'item_id',
    'item_category': 'item_category_id',
    'item_manipulation_type': 'id',
    'item_phase': 'model',
    'key': 'item_id',
    'key_subtype': 'key_subtype_id',
    'key_type': 'key_type_id',
    'keyring': 'item_id',
    'keyring_type': 'keyring_type_id',
    'melee_weapon': 'item_id',
    'melee_weapon_type': 'melee_weapon_type_id',
    'misc': 'item_id',
    'misc_subtype': 'misc_subtype_id',
    'misc_type': 'misc_type_id',
    'missile_weapon': 'item_id',
    'missile_weapon_class2ammo_class': 'missile_weapon_class_id',
    'missile_weapon_type': 'missile_weapon_type_id',
    'npc_tool': 'item_id',
    'npc_tool_subtype': 'npc_tool_subtype_id',
    'npc_tool_type': 'npc_tool_type_id',
    'ointment_item': 'item_id',
    'ointment_item_subtype': 'ointment_item_subtype_id',
    'ointment_item_type': 'ointment_item_type_id',
    'pickable_area_desc': 'id',
    'pickable_area_material': 'material_name',
    'pickable_item': 'item_id',
    'player_item': 'item_id',
    'potion': 'item_id',
    'questible_item': 'item_id',
    'recipe': 'recipe_id',
    'recipe_ingredient': 'item_id',
    'recipe_step': 'ui_text',
    'recipe_substep': ['recipe_id', 'recipe_step_id', 'recipe_substep_id'],
    'weapon': 'item_id',
    'weapon2weapon_preset': 'item_id',
    'weapon_attachment_slot': 'weapon_attachment_slot_id',
    'weapon_class': 'weapon_class_id',
    'weapon_equip_slot': 'weapon_equip_slot_id',
    'weapon_preset': 'weapon_preset_id',
    'weapon_sub_class': 'weapon_sub_class_id',

    # Data/Libs/Tables/prefab
    # -------------------------------------------------------------------------
    'prefab_phase': ['order', 'prefabfullname'],
    'prefab_phase_category': 'prefab_phase_category_id',

    # Data/Libs/Tables/quest
    # -------------------------------------------------------------------------
    'exp_change': 'exp_change_id',
    'money_change': 'money_change_id',
    'quest': 'quest_id',
    'quest2skald_subchapter': ['quest_id', 'skald_subchapter_id'],
    'quest_asset': ['quest_asset_id', 'quest_id'],
    'quest_function': 'function',
    'quest_function_param': 'objective_function_id',
    'quest_item': ['quest_id', 'item_id'],
    'quest_npc': ['quest_id', 'soul_id'],
    'quest_objective': ['quest_id', 'objective_id'],
    'quest_place': ['entity', 'quest_id'],
    'quest_reward_achievement': ['quest_id', 'objective_id', 'statistic_id'],
    'quest_reward_exp': ['quest_id', 'objective_id', 'rpg_attr'],
    'quest_reward_item': ['quest_id', 'objective_id', 'item_id'],
    'quest_reward_money': 'quest_reward_money_id',
    'quest_reward_perk': 'quest_reward_perk_id',
    'quest_reward_reputation': 'quest_reward_reputation_id',
    'quest_reward_script': ['quest_id', 'objective_id', ''],
    'quest_soul_mortality': ['quest_id', 'soul_id'],
    'quest_statistic': ['quest_id', 'statistic_id'],
    'quest_tracked_asset': ['quest_id', 'objective_id', 'quest_asset_id'],
    'quest_transition': ['quest_id', 'from_objective_id', 'to_objective_id'],
    'quest_type': 'quest_type_id',
    'quest_vip_npc': ['quest_id', 'quest_npc_id'],

    # Data/Libs/Tables/rpg
    # -------------------------------------------------------------------------
    'achievement': 'achievement_id',
    'achievement_rule': 'achievement_id',
    'angriness_enum': 'angriness_enum_id',
    'buff': 'buff_id',
    'buff_class': 'buff_class_id',
    'buff_lifetime': 'buff_lifetime_id',
    'combat_shout_type': 'combat_shout_type_id',
    'document_required_skill': 'item_id',
    'document_requirement': 'item_id',
    'document_reward': 'item_id',
    'document_reward_perk': 'item_id',
    'faction': 'faction_id',
    'game_over': 'game_over_id',
    'gender': 'gender_id',
    'hobby': 'hobby_id',
    'horse_irritation': 'horse_irritation_id',
    'location': 'location_id',
    'location2perk': 'perk_id',
    'location_category': 'location_category_id',
    'metarole': 'metarole_id',
    'morale_change': 'morale_change_id',
    'perk': 'perk_id',
    'perk2perk_exclusivity': 'first_perk_id',
    'perk_buff': 'buff_id',
    'perk_buff_override': 'perk_id',
    'perk_codex': 'perk_id',
    'perk_combo_step': 'perk_id',
    'perk_companion': 'perk_id',
    'perk_recipe': 'perk_id',
    'perk_script': 'perk_id',
    'perk_soul_ability': 'perk_id',
    'perk_special_riposte': 'perk_id',
    'poi_type': 'poi_type_id',
    'poi_type2perk': 'perk_id',
    'race': 'race_id',
    'reading_spot_type': 'reading_spot_type_id',
    'reputation_change': 'reputation_change_id',
    'reputation_condition': 'reputation_condition_id',
    'rich_presence': 'rich_presence_id',
    'role': 'role_id',
    'rpg_movement_type': 'rpg_movement_type_id',
    'rpg_param': 'rpg_param_key',
    'rpg_sound': 'rpg_sound_id',
    'skill': 'skill_id',
    'skill2item_category': 'skill_id',
    'skill_check_difficulty': 'skill_check_difficulty_id',
    'sleeping_spot_type': 'sleeping_spot_type_id',
    'social_class': 'social_class_id',
    'soul': 'soul_id',
    'soul2hobby': 'soul_id',
    'soul2inventory': 'soul_id',
    'soul2metarole': 'soul_id',
    'soul2perk': 'soul_id',
    'soul2role': 'soul_id',
    'soul2skill': 'soul_id',
    'soul_archetype': 'soul_archetype_id',
    'soul_archetype_movement': 'soul_archetype_id',
    'soul_class': 'soul_class_id',
    'soul_slot2health': 'soul_id',
    'soul_slot2weapon_health': 'soul_id',
    'statistic': 'statistic_id',
    'statistic_group': 'statistic_group_id',
    'superfaction': 'superfaction_id',
    'superfaction2superfaction_relationship': ['from_superfaction_id', 'to_superfaction_id'],
    'v_rich_presence_text': ['iso_code', 'string_name'],
    'v_soul2role_metarole': 'soul_id',
    'v_soul_character_data': 'soul_id',

    # Data/Libs/Tables/shop
    # -------------------------------------------------------------------------
    'shop': 'shop_id',
    'shop2item': ['shop_id', 'item_id'],
    'shop_type2item': ['shop_type_id', 'item_id'],
    'shopkeeper': 'keeper_id',

    # Data/Libs/Tables/skald
    # -------------------------------------------------------------------------
    'skald_objective': 'skald_element_id',
    'skald_objective_string': ['skald_element_id', 'string_name'],
    'skald_objective_string_type': 'skald_objective_string_type_id',
    'skald_quest_string': 'string_name',
    'skald_quest_string_type': 'skald_quest_string_type_id',

    # Data/Libs/Tables/text
    # -------------------------------------------------------------------------
    'branch': 'skald_element_id',
    'dialogue_command_hearing': 'sequence_line_id',
    'dialogue_functions': 'function_name',
    'dialogue_hearing': 'dialogue_hearing_id',
    'dialogue_mood': 'dialogue_mood_id',
    'response': 'sequence_line_id',
    'sequence': 'sequence_id',
    'sequence2quest_objective': ['sequence_id', 'quest_id', 'objective_id'],
    'sequence_flowchart': 'flowchart_name',
    'sequence_line': 'sequence_line_id',
    'sequence_line_type': 'sequence_line_type_id',
    'topic': 'topic_id',
    'topic2decision_role': ['role_id', 'topic_id'],
    'topic2sequence': ['sequence_id', 'topic_id'],
    'topictorole': ['role_id', 'topic_id'],
    'v_branch': 'skald_element_id',
    'v_dialogue_commands': ['sequence_line_id', 'who'],
    'v_response_wave_file_recorded': ['sequence_line_id', 'wave_file'],
    'v_topic2subchapter_id': ['skald_subchapter_id', 'start_topic'],
    'v_voice_abbreviation': 'voice_id',

    # Data/Libs/Tables/ui
    # -------------------------------------------------------------------------
    'cf_backer_ingame': 'cf_backer_id',
    'credit_layout': 'credit_layout_id',
    'credit_people': 'credit_people_id',
    'credit_role': 'credit_role_id',
    'credit_role2language': ['credit_role_id', 'language_id'],
    'infotext_category': 'name',
    'skiptime': 'skiptime_id',
    'ui_local_maps': 'location_id',
    'ui_map_label': 'ui_map_label_id',
    'video_language2audio_track': 'language_id',
}


class Utils:
    @staticmethod
    def strip_whitespace(text):
        if text:
            text = re.sub('\s+', ' ', text)
            return text.strip()

    @staticmethod
    def get_signature_by_filename(filename, *, keymap=SIGNATURES):
        file_name, file_ext = os.path.splitext(filename)
        for key in keymap.keys():
            if key == file_name:
                return keymap[key]

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
