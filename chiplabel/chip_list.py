#!/usr/bin/env python3
# chip_list.py
#
import logging
import os
from pathlib import Path
import yaml
from . import chip

log = logging.getLogger(__name__)

class ChipList:
    _chip_list = {}
    _global_name_dict = {}

    def find_chip(self, chip_id):
        log.debug('find_chip(%s)', chip_id)
        if '/' in chip_id: # scoped chip id
            return self._chip_list.get(chip_id)
        return self._global_name_dict.get(chip_id)

    def clear(self):
        _chip_list = {}
        _global_name_dict = {}

    def load(self, path):
        log.debug('load_chip_list(%s)', path)
        if os.path.isfile(path):
            self._load_single_file(path)
        elif os.path.isdir(path):
            for file in os.listdir(path):
                if file.endswith(".yaml"):
                    fullpath = os.path.normpath(os.path.join(path, file))
                    self._load_single_file(fullpath)
        else:
            raise IOError('input must be a file or directory')

    def _add_aliases(self, chip, family):
        id = chip.unscoped_id
        if family == '7400':
            log.debug('Adding 7400-family aliases')
            if id[:2] != '74':
                log.error('Chip is missing 74 prefix: %s, skipping aliases', id)
            else:
                FAMILIES = ['L', 'H', 'S', 'LS', 'AS', 'ALS', 'F', # Bipolar
                            'C', 'HC', 'HCT', 'AC', 'ACT', # CMOS
                            'ACQ', 'AHC', 'ALVC', 'ALVT', 'AUC', # CMOS overkill
                            'AUP', 'AVC', 'AXC', 'FC', 'FCT', 'LCX', 
                            'LV', 'LVC', 'LVT', 'LVQ', 'LVX', 'VHC']
                names = [f'{id[:2]}{fam}{id[2:]}' for fam in FAMILIES]
                for name in names:
                    self._global_name_dict[name] = chip.create_alias(name)
                log.debug('Added %d aliases: %s', len(names), names)
        else:
            log.warning('Unknown family: %s for chip %s', family, chip.scoped_id)

    def _load_single_file(self, filename):
        log.debug('load_chip_list_file(%s)', filename)
        library_name = Path(filename).stem
        log.debug('library_name: %s', library_name)

        chip_list = {}
        skipped = 0
        with open(filename, 'r', encoding='utf8') as ymlfile:
            yaml_chips = yaml.safe_load(ymlfile)
            for id, yaml_chip in yaml_chips.items():
                log.debug('processing: %s, data: %s', id, yaml_chip)
                string_id = str(id)
                scoped_id = f'{library_name}/{string_id}'
                log.debug('Processing id=%s', scoped_id)
                if string_id[0] == '_':
                    log.debug("Skipping id=%s", scoped_id)
                    skipped += 1
                    continue
                spacing = 6

                if 'type' in yaml_chip and yaml_chip['type'] == 'wide':
                    spacing = 12
                try:
                    new_chip = chip.Chip(string_id, len(yaml_chip['pins']),
                        library=library_name,
                        rowSpacing=spacing)

                    if 'name' in yaml_chip:
                        new_chip.name = str(yaml_chip['name'])
                    if 'description' in yaml_chip:
                        new_chip.description = str(yaml_chip['description'])

                    new_chip.set_pins(yaml_chip['pins'])
                    chip_list[scoped_id] = new_chip

                    # Add to raw chip list for global searches
                    if string_id in self._global_name_dict:
                        log.warning('Duplicate global chip id [%s], use scoped name [%s] for lookup', string_id, scoped_id)
                    self._global_name_dict[string_id] = new_chip

                    if 'family' in yaml_chip:
                        self._add_aliases(new_chip, str(yaml_chip['family']))

                except chip.Error as err:
                    log.error('Error adding chip [%s]: %s, skipping',
                        scoped_id, err)
                    skipped += 1
        log.info(f'Loaded %d chips from %s %s', len(chip_list), filename,
            f'({skipped} skipped)' if skipped else '')

        self._chip_list.update(chip_list)

    def __len__(self):
        return len(self._chip_list)

    def __iter__(self):
        return self._chip_list.values().__iter__()

    def __getitem__(self, item):
        return self.find_chip(item)

    @property
    def names(self):
        return self._chip_list.keys().__iter__()

def main():
    logging.basicConfig(level=logging.DEBUG)

    chip_list = ChipList()
    # chip_list.load('chips/chips.yaml')
    # for chip in chip_list:
    #     chip.print_ASCII()
    #     print()

    # chip = chip_list['chips/bad']
    # print(chip)

    # chip = chip_list['chips/DAC0808']
    # print(chip)

    chip_list = ChipList()
    chip_list.load('chips/7400.yaml')
    #print(chip)

if __name__ == '__main__':
    main()