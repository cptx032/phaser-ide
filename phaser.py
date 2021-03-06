#!/usr/bin/env python
# coding: utf-8

import sys
import core
PYTHON_3 = sys.version_info.major == 3
if PYTHON_3:
    from tkinter import filedialog as tkFileDialog
    import tkinter
else:
    import tkFileDialog
    import Tkinter
from windows import *
from windows.shortcuts import *
import components as comp
import posixpath
import importlib
import json
import random
import string
import logiceditor
import logiceditor.sensors
import logiceditor.controllers
import logiceditor.actuators
import boring
import boring.widgets
import windows.newproject
import windows.about
import windows.scene
import windows.assets
import boring.ttk as ttk
import boring.menus

VErSIOn = 'alpha'

class PhaserEditor(boring.Window):
    def __init__(self):
        self.__current_project = None
        # stores the canvas itself
        # the key is the scene name
        self.canvases = {}
        # stores all sprite of each canvas
        # the key is the scene name
        self.sprite_canvases = {}
        self.actual_canvas = None
        # stores all logic editors by scene
        self.logic_editors = {}

        Tkinter.Tk.__init__(self)
        ttk.Style().theme_use('clam')
        self['bg'] = boring.BG_COLOR
        self.geometry('%dx%d' % (1200, 600))

        # for drag loacking
        self.kmap = dict()
        self.__pressing_x = False
        self.__pressing_y = False
        self.bind('<Any-KeyPress>', self.__press_key, '+')
        self.bind('<Any-KeyRelease>', self.__release_key, '+')

        self.bind('<Control-n>', self.new_project, '+')
        self.bind('<Control-m>', self._add_scene_btn_handler, '+')
        self.bind('<Control-x>', self._add_sprite_btn_handler, '+')
        self.bind('<Control-s>', self.save_project_as_json, '+')
        self.bind('<Control-o>', self.open_json_project, '+')
        self.bind('<Alt-p>', self.show_project_properties, '+')

        self.left_panel = boring.widgets.Frame(self)
        self.left_panel.pack(
            fill='y',
            side='left'
        )

        ################ LEFT PANEL
        self.left_frame = boring.widgets.Frame(self.left_panel)
        self.left_frame_top = boring.widgets.Frame(self.left_frame)
        self.scene_manager = boring.widgets.ScrollableExtendedListbox(
            self.left_frame,
            width=250,
            unique_titles=True
        )
        self.scene_manager.bind('<1>', self.__on_select_scene, '+')
        self.add_scene_btn = boring.widgets.Button(
            self.left_frame_top,
            text='+',
            width=20,
            command=self._add_scene_btn_handler
        )
        self.del_scene_btn = boring.widgets.Button(
            self.left_frame_top,
            text='-',
            width=20,
            command=self._del_scene_btn_handler
        )
        boring.widgets.Label(self.left_frame_top, text='Scenes').pack(
            anchor='nw',
            side='left'
        )
        self.add_scene_btn.pack(
            side='right',
            anchor='ne',
            padx=1
        )
        self.del_scene_btn.pack(
            side='right',
            anchor='ne',
            padx=1
        )
        self.left_frame_top.pack(
            anchor='nw',
            padx=5,
            pady=5,
            fill='both'
        )
        self.left_frame.pack(
            fill='y',
            expand='yes'
        )

        self.scene_manager.pack(
            side='left',
            expand='yes',
            fill='y',
            anchor='nw'
        )

        ################ RIGHT PANEL
        self.right_frame = boring.widgets.Frame(self.left_panel)
        self.right_frame_top = boring.widgets.Frame(self.right_frame)
        self.assets_manager = boring.widgets.ScrollableExtendedListbox(
            self.right_frame,
            width=250,
            unique_titles=True
        )
        boring.widgets.Label(self.right_frame_top, text='Assets').pack(
            anchor='nw',
            side='left'
        )
        self.right_frame_top.pack(
            anchor='nw',
            padx=5,
            pady=5,
            fill='both'
        )

        self.add_sprite_btn = boring.widgets.Button(
            self.right_frame_top,
            text='+', width=20,
            command=self._add_sprite_btn_handler
        )
        self.del_sprite_btn = boring.widgets.Button(
            self.right_frame_top,
            text='-',
            width=20,
            command=self._del_sprite_btn_handler
        )
        self.add_sprite_btn.pack(
            side='right',
            anchor='ne',
            padx=1)
        self.del_sprite_btn.pack(
            side='right',
            anchor='ne',
            padx=1
        )
        self.assets_manager.pack(
            side='left',
            expand='yes',
            fill='y',
            anchor='nw'
        )
        self.right_frame.pack(
            fill='y',
            expand='yes'
        )

        ################ RIGHT PANEL
        self.canvas_frame = boring.widgets.Frame(self)
        self.canvas_frame.pack(
            expand='yes'
        )

        ############################
        self.center()
        self.bind('<Delete>', self.__delete_sprite, '+')
        self.bind('<Up>', self.__up_key, '+')
        self.bind('<Down>', self.__down_key, '+')
        self.bind('<Right>', self.__right_key, '+')
        self.bind('<Left>', self.__left_key, '+')
        self.focus_force()

        ############################### Command windows
        self.__menu_items = [
            dict(
                name='Create/New Project',
                command=self.new_project,
                subtitle='Creates a new project'
            ),
            dict(
                name='Open project from JSON',
                command=self.open_json_project,
                subtitle='Open a json project'
            ),
            dict(
                name='Save project as JSON',
                command=self.save_project_as_json,
                subtitle='Save a json with project (using absolute paths)'
            ),
            dict(
                name='Show project properties',
                command=self.show_project_properties,
                subtitle='Shows a window with the project properties'
            ),
            dict(
                name='Quit/Close application',
                command=lambda event : self.quit(),
                subtitle='Closes the application'
            ),
            dict(
                name='Show Logic Editor',
                command=self.show_logic_editor,
                subtitle='The logic editor allows your edit the logic bricks'
            ),
            dict(
                name='Show Shortcuts',
                command=self.show_shortcuts_window,
                subtitle='Show all available shortcuts'
            ),
            dict(
                name='About',
                command=self.show_about_window,
                subtitle='Show about window'
            ),
            dict(
                name='Clear canvas scroll',
                command=self.clear_cur_canvas_scroll,
                subtitle='Clears the canvas scroll'
            ),
        ]
        self.__menu = boring.menus.CommandChooserWindow(self)
        self.bind(
            '<Key-space>',
            lambda evt: self.__menu.popup(self.__menu_items),
            '+'
        )
        self.__menu.withdraw()
        self.__load_plugins()
        self.set_title()

    def clear_cur_canvas_scroll(self, event=None):
        self.cur_canvas().clear_scroll()

    def __release_key(self, event):
        '''
        called when you release any key (keyboard)
        '''
        self.kmap[event.keysym] = False

    def __press_key(self, event):
        '''
        called when you release any key (keyboard)
        '''
        self.kmap[event.keysym] = True

    @property
    def current_project(self):
        return self.__current_project

    @current_project.setter
    def current_project(self, value):
        self.__current_project = value
        self.set_title()

    def set_title(self):
        self.title('Phaser - %s - version: %s' % ('No project loaded' if not self.current_project else self.current_project.name, VErSIOn))

    def save_project_as_json(self, event=None):
        '''
        called when you press ctrl + s
        '''
        if self.current_project:
            json_dict = self.current_project.get_dict()
            json_dict.update(
                scenes=self.get_scenes_dict(),
                assets=self.get_assets_dict()
            )
            filename = tkFileDialog.asksaveasfilename()
            if filename:
                f = open(filename, 'w')
                f.write( json.dumps(json_dict) )
                f.close()
                boring.dialog.MessageBox.info(
                    parent=self, title='Success',
                    message='Project saved!'
                )

    def __gen_sprite_name(self):
        '''
        generates a random name
        '''
        return ''.join( [random.choice(string.letters) for i in xrange(15)] )

    def __get_file_content(self, file_path): # TODO: utils
        '''
        returns the content of file
        '''
        fs = open(file_path)
        content = fs.read()
        fs.close()
        return content

    def open_json_project(self, event=None):
        '''
        called when you press ctrl + o
        '''
        if self.current_project and (not boring.dialog.OkCancel(self, 'A loaded project already exists. Do you wish to continue?').output):
            return
        self.__reset_ide()

        file_opt = dict(filetypes=[('JSON Project', '.json')])
        file_name = tkFileDialog.askopenfilename(parent=self, **file_opt)
        if file_name:
            try:
                json_project = json.loads( self.__get_file_content(file_name) )
                self.current_project = core.PhaserProject(json_project)
                # the assets must be loaded first
                # because the scene loading will try get assets information
                # to put the sprite in ide
                self.load_assets_from_dictlist( json_project['assets'] )
                self.load_scenes_from_dictlist( json_project['scenes'] )
            except Exception, e:
                boring.dialog.MessageBox.warning(
                    parent=self,
                    title='Error loading JSON project',
                    message='The JSON format is wrong'
                )
                raise e

    def load_scenes_from_dictlist(self, _list):
        '''
        fill the ide with scenes in '_list'
        '''
        for scene in _list:
            self.add_scene( scene['name'] )
            for sprite in scene['sprites']:
                component = self.add_sprite(
                    scene['name'], sprite
                )

    def load_assets_from_dictlist(self, _list):
        '''
        fill the ide with assets in '_list'
        '''
        for asset in _list:
            self.add_asset( asset )

    def get_assets_dict(self):
        '''
        returns a list where each item is a dict describing
        the asset.
        used when you save the project
        '''
        result = []
        for asset in self.assets_manager.get_all():
            result.append( asset.details )
        return result

    def get_scenes_dict(self):
        '''
        returns a list where each item is a dict describing
        the scene.
        used when you save the project
        '''
        result = []
        for scenename in self.sprite_canvases.keys():
            d = {}
            result.append({
                'name': scenename,
                'sprites': self.get_sprites_dict(self.sprite_canvases[scenename])
            })
        return result

    def get_scene_list(self):
        '''
        returns a list with the name of all scenes
        '''
        return self.canvases.keys()

    def get_sprites_dict(self, sprites):
        '''
        sprites: a list of sprites
        this function receive a list of components
        and transforms them in a list where each item
        is a dict describind it
        '''
        result = []
        for sprite in sprites:
            if type(sprite) == comp.ImageComponent:
                result.append({
                    'name': sprite.name,
                    'assetname': sprite.assetname,
                    'x': sprite.x,
                    'y': sprite.y
                })
            elif type(sprite) == comp.SpriteComponent:
                result.append({
                    'name': sprite.name,
                    'assetname': sprite.assetname,
                    'x': sprite.x,
                    'y': sprite.y,
                    'framerate': sprite.framerate,
                    'autoplay': sprite.autoplay
                })
        return result

    def __load_plugins(self):
        '''
        the "plugin system" is very simple:
        exist a file named '.plugins' where each line
        is a name of a python module. Each module is imported
        in start of phaser ide. The module must have 3 things:
        1. a attribute named 'title' (this name will be putted in
        menu)
        2. a method 'init', called after import
        3. a method 'execute' called in the click of menu
        '''
        a = open('./.plugins')
        modules = a.readlines()
        a.close()
        def get_func(mod):
            def _func(*args):
                mod.execute(self)
            return _func
        for i in modules:
            try:
                mod_name = i.replace('\n', '')
                mod = importlib.import_module('plugins.' + mod_name)
                mod.init(self)
                self.__menu_items.append(dict(
                    name=mod.title,
                    command=get_func(mod),
                    subtitle='Plugin'
                ))
            except ImportError:
                boring.dialog.MessageBox.warning(
                    parent=self,
                    message='Was not possible load the module "*%s*"' % (mod_name),
                    title='Plugin Error'
                )

    def update_canvases(self):
        '''
        updates the bg, width and height of all canvases
        '''
        for canvas in self.canvases.values():
            canvas['bg'] = self.current_project.bgcolor
            canvas['width'] = self.current_project.width
            canvas['height'] = self.current_project.height

    def project_is_loaded(self):
        '''
        returns true if project is loaded, else
        shows a message and returns false
        '''
        if self.current_project:
            return True
        boring.dialog.MessageBox.warning(
            parent=self,
            title='No project found',
            message='No project found'
        )
        return False

    def cur_canvas(self):
        '''
        returns the actual canvas instance shown in the screen
        '''
        return self.canvases.get(self.actual_canvas, None)

    def __reset_all_canvas(self):
        '''
        remove from screen all canvas
        '''
        for i in self.canvases:
            self.canvases[i].pack_forget()
        self.canvases = {}
        self.sprite_canvases = {}
        self.actual_canvas = None

    def show_logic_editor(self, event=None):
        if self.current_project and self.actual_canvas:
            self.logic_editors[self.actual_canvas].show()

    ################ SCENES
    def __on_select_scene(self, sceneitem):
        '''
        called when the user clicks in a scene
        in scene manager
        '''
        scene_name = sceneitem.title
        if (scene_name != self.actual_canvas and self.actual_canvas != None) or self.actual_canvas == None:
            if self.actual_canvas:
                self.canvases[self.actual_canvas].pack_forget()
            self.actual_canvas = scene_name
            self.cur_canvas().pack()

    def _add_scene_btn_handler(self, event=None):
        '''
        called when user clicks over add_scene_button
        '''
        if not self.project_is_loaded():
            return

        asw = windows.scene.AddSceneWindow(self)
        if asw.output:
            try:
                self.add_scene(asw.output['name'])
            except boring.widgets.DuplicatedExtendedListboxItemException:
                boring.dialog.MessageBox.warning(
                    parent=self,
                    title='DuplicatedExtendedListboxItemException',
                    message='a scene in project already contains this name')

    def add_scene(self, name):
        '''
        add an icon in scene manager and fills the canvas
        '''
        self.scene_manager.add_item(
            name, 'scene', 'icons/folder.png',
            before_click=self.__on_select_scene
        )
        ca = boring.widgets.ExtendedCanvas(
            self.canvas_frame,
            width=self.current_project.width,
            height=self.current_project.height,
            bg=self.current_project.bgcolor,
            draggable=True
        )
        ca.pack(anchor='sw', side='left')
        self.canvases[name] = ca
        # creating the logic editor for this scene
        self.logic_editors[name] = logiceditor.LogicEditor(self)
        self.logic_editors[name].hide()
        # the list of sprites of this scene is a empty list
        self.sprite_canvases[name] = []
        if self.actual_canvas:
            self.cur_canvas().pack_forget()
        self.actual_canvas = name
        # put focus in actual canvas
        self.scene_manager.desselect_all()
        self.scene_manager.select_last()

    def _del_scene_btn_handler(self):
        '''
        called when user clicks over del_scene_button
        '''
        if not self.project_is_loaded():
            return

        selection = self.scene_manager.get_selected()
        if selection:
            scene_name = selection.title
            if boring.dialog.OkCancel(self,
                'The scene *%s* will be delete. Are you sure?' % (scene_name),
                title='Are you sure?').output:

                self.scene_manager.remove_by_title(scene_name)
                self.canvases[scene_name].pack_forget()
                del self.canvases[scene_name]
                self.actual_canvas = None

    ################ ASSETS
    SUPPORTED_IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'gif', 'tiff']
    SUPPORTED_SOUND_FILES = ['mp3', 'ogg', 'wav']
    def get_file_name(self):
        '''
        opens a file dialog for file selection and returns
        the path
        '''
        image_ext = '.' + ' .'.join(PhaserEditor.SUPPORTED_IMAGE_TYPES)
        sound_ext = '.' + ' .'.join(PhaserEditor.SUPPORTED_SOUND_FILES)
        file_opt = dict(filetypes=[('Image Files', image_ext), ('Sound Files', sound_ext)])
        return tkFileDialog.askopenfilename(parent=self, **file_opt)

    def _add_sprite_btn_handler(self, event=None):
        '''
        called when user clicks over add_sprite_btn
        '''
        if not self.project_is_loaded():
            return

        file_name = self.get_file_name()
        if not file_name:
            return
        ext = posixpath.basename(file_name).split('.')[-1].lower()
        if file_name:
            if ext in PhaserEditor.SUPPORTED_SOUND_FILES:
                self.__add_sound_asset(file_name)
            elif ext in PhaserEditor.SUPPORTED_IMAGE_TYPES:
                self.__add_image_asset(file_name)

    def __add_sound_asset(self, file_name):
        '''
        called after select a music file
        '''
        asaw = AddSoundAssetWindow(self, path=file_name)
        if asaw.output:
            try:
                self.assets_manager.add_item(asaw.output['name'],
                    'sound', 'icons/headphone.png')
            except DuplicatedExtendedListboxItemException:
                boring.diloag.MessageBox.warning(
                    parent=self,
                    title='DuplicatedExtendedListboxItemException',
                    message='a asset in project already contains this name')

    def __add_image_asset(self, file_name):
        '''
        called after select a image file
        '''
        aiaw = windows.assets.AddImageAssetWindow(self, path=file_name)
        if aiaw.output:
            try:
                self.add_asset( aiaw.output )
            except DuplicatedExtendedListboxItemException:
                boring.diloag.MessageBox.warning(
                    parent=self,
                    title='DuplicatedExtendedListboxItemException',
                    message='a asset in project already contains this name')

    def add_asset(self, details):
        '''
        add a asset in IDE
        details must be a dict describeing the asset
        can raises a DuplicatedExtendedListboxItemException
        use in loading json project
        '''
        if details['type'] in ('image', 'sprite'):
            item = self.assets_manager.add_item(details['name'],
                'image', 'icons/image.png')
            item.bind('<Double-Button-1>', lambda event : self.__dbl_click_image_asset(item), '+')
        item.details = details

    def _del_sprite_btn_handler(self):
        '''
        called when user clicks over del_sprite_btn
        '''
        if not self.project_is_loaded():
            return

        selection = self.assets_manager.get_selected()
        if selection:
            if boring.dialog.OkCancel(self,
                'The asset *%s* will be delete and with him all yours sprites too. Are you sure?' % (selection.title),
                title='Are you sure?').output:
                self.assets_manager.remove_by_title(selection.title)
                self.remove_asset_by_name(selection.title)

    def add_sprite(self, scenename, _dict):
        '''
        puts in canvas of scene named 'scenename' a component

        return the sprite
        '''
        asset = self.get_asset_details_by_name( _dict['assetname'] )

        kws = dict(**_dict)

        kws.update(
            canvas = self.canvases[scenename],
            path = asset['path'],
            ide = self
        )
        
        sprite = None

        if asset['type'] == 'image':
            sprite = comp.ImageComponent( **kws )
        elif asset['type'] == 'sprite':
            kws.update(
                sprite_width = asset['sprite_width'],
                sprite_height = asset['sprite_height']
            )
            sprite = comp.SpriteComponent( **kws )
        # binds common events
        if sprite:
            sprite.details = _dict
            self.__add_sprite_to_canvas( sprite )
        return sprite

    def __dbl_click_image_asset(self, item):
        '''
        called when user double clicks in the asset image button
        '''
        if not self.actual_canvas:
            boring.dialog.MessageBox.warning(
                    parent=self,
                    title='No scene specified',
                    message='Select/create a scene to put sprite')
            return

        cx, cy = self.cur_canvas().center
        # scenename, _dict
        kws = dict(
            name = self.__gen_sprite_name(),
            x = cx, y = cy,
            path = item.details['path'],
            assetname = item.title
        )
        if item.details['type'] == 'sprite':
            kws.update(
                sprite_width = item.details['sprite_width'],
                sprite_height = item.details['sprite_height'],
                framerate = 10,
                autoplay = True
            )
        self.add_sprite(
            self.actual_canvas, # the actual_canvas field is the name of scene
            kws
        )

    def __add_sprite_to_canvas(self, sprite):
        '''
        called when the user double clicks in a assets in assets manager
        '''
        self.sprite_canvases[self.actual_canvas].append( sprite )
        sprite.bind('<1>', lambda evt: self.__select_sprite(sprite), '+')

    def desselect_all_sprites(self):
        for i in self.sprite_canvases[self.actual_canvas]:
            i.selected = False
            # if has rectangle bounds
            if i.bounds:
                i.bounds.style['outline'] = boring.drag.DRAG_CONTROL_STYLE['fill']
            i.bounds.update()
            i.update()

    def __select_sprite(self, sprite):
        '''
        called when the user clicks in a sprite
        '''
        self.desselect_all_sprites()
        sprite.selected = True
        sprite.bounds.style['outline'] = 'red'
        sprite.bounds.update()
        sprite.update()

    def get_selected_sprite(self):
        '''
        returns the selected sprite
        '''
        for i in self.sprite_canvases[self.actual_canvas]:
            if hasattr(i, 'selected') and i.selected:
                return i
        return None

    def __delete_sprite(self, evt):
        '''
        called when user clicks 'del' key
        '''
        selected = self.get_selected_sprite()
        if selected:
            self.sprite_canvases[self.actual_canvas].remove(selected)
            selected.bounds.delete()
            selected.lower_right.delete()
            selected.delete()

    def __right_key(self, evt):
        '''
        called when user clicks 'up' key
        '''
        selected = self.get_selected_sprite()
        if selected:
            selected.x += 1

    def __left_key(self, evt):
        '''
        called when user clicks 'up' key
        '''
        selected = self.get_selected_sprite()
        if selected:
            selected.x -= 1

    def __up_key(self, evt):
        '''
        called when user clicks 'up' key
        '''
        selected = self.get_selected_sprite()
        if selected:
            selected.y -= 1

    def __down_key(self, evt):
        '''
        called when user clicks 'up' key
        '''
        selected = self.get_selected_sprite()
        if selected:
            selected.y += 1

    def remove_asset_by_name(self, name):
        '''
        remove a asset and all 'childs' (sprites)
        '''
        sprites_to_delete = {}
        for item in self.scene_manager.get_all():
            scene_name = item.title
            if not sprites_to_delete.has_key(scene_name):
                sprites_to_delete[scene_name] = []
            for sprite in self.sprite_canvases[scene_name]:
                if sprite.assetname == name:
                    sprites_to_delete[scene_name].append(sprite)
        for item in self.scene_manager.get_all():
            scene_name = item.title
            for i in sprites_to_delete[scene_name]:
                self.sprite_canvases[scene_name].remove(i)
                i.delete()

    def get_asset_details_by_name(self, name):
        '''
        returns the details of a asset gived your name
        '''
        for i in self.assets_manager.get_all():
            if i.details['name'] == name:
                return i.details
        return None

    ################### Menu events
    def show_shortcuts_window(self, event=None):
        '''
        called when you click Help > shortcuts
        '''
        ShortcutsWindow(self)

    def show_about_window(self, event=None):
        windows.about.AboutWindow(self)

    def new_project(self, event=None):
        if self.current_project and \
                (not boring.dialog.OkCancel(
                    self, 'A loaded project already exists. Do you wish to continue?'
                ).output):
            return
        npw = windows.newproject.NewProjectWindow(self)
        if npw.output:
            self.__reset_ide()
            self.current_project = core.PhaserProject(npw.output)
            self.__initial_scenes_and_assets()

    def __initial_scenes_and_assets(self):
        '''
        called in new_project
        '''
        self.__create_initial_assets()
        self.__create_boot_scene()
        self.add_scene('preload')
        self.add_scene('mainscene')

    def __create_initial_assets(self):
        '''
        called in __initial_scenes_and_assets
        '''
        self.add_asset({
            'type': 'image',
            'path': 'assets/default_loading.png',
            'name': 'default_loading'
        })

    def __create_boot_scene(self):
        '''
        called in __initial_scenes_and_assets
        '''
        self.add_scene('boot')
        boot_logic_editor = self.logic_editors['boot']
        preload = logiceditor.sensors.PreloadSensorDrawWindow(boot_logic_editor)
        preload.x = 20
        preload.y = 100

        load_assets = logiceditor.actuators.LoadAssetsActuatorDrawWindow(
            boot_logic_editor, get_assets_func=self.get_assets_dict
        )
        load_assets.add_asset('default_loading')
        load_assets.x = 550
        load_assets.y = 100

        self.logic_editors['boot'].add_connect_by_AND(preload, load_assets)

        boot_create = logiceditor.sensors.SignalSensorDrawWindow(boot_logic_editor)
        boot_create.x = 20
        boot_create.y = 200

        code_actuator = logiceditor.actuators.CodeActuatorDrawWindow(boot_logic_editor)
        code_actuator.x = 550
        code_actuator.y = 200
        # TODO: colocar isso num arquivo externo
        code_actuator.set_code('''
this.scale.scaleMode = Phaser.ScaleManager.SHOW_ALL;
this.game.stage.scale.forceLandscape = true;

this.scale.pageAlignHorizontally = true;
this.scale.pageAlignVertically = true;
this.game.stage.backgroundColor = {bgcolor};
this.game.scale.forceOrientation(true, false);

this.game.scale.enterIncorrectOrientation.add(this.handleIncorrect);
''')
        self.logic_editors['boot'].add_connect_by_AND(boot_create, code_actuator)

        signal_load_scene = logiceditor.sensors.SignalSensorDrawWindow(boot_logic_editor)
        signal_load_scene.x = 20
        signal_load_scene.y = 300

        load_scene = logiceditor.actuators.LoadSceneActuatorDrawWindow(
            boot_logic_editor, get_scene_func=self.get_scene_list
        )
        load_scene.value = 'preload'
        load_scene.x = 550
        load_scene.y = 500

        self.logic_editors['boot'].add_connect_by_AND(signal_load_scene, load_scene)

    def __reset_ide(self):
        '''
        clears all canvases, scenes, sprite etc...
        '''
        self.current_project = None
        self.scene_manager.delete_all()
        self.assets_manager.delete_all()
        self.__reset_all_canvas()
        self.__destroy_all_logiceditors()

    def __destroy_all_logiceditors(self):
        for scenename in self.logic_editors.keys():
            self.logic_editors[scenename].destroy()
        self.logic_editors = dict()

    def show_project_properties(self, event=None):
        if self.current_project:
            npw = windows.newproject.NewProjectWindow(
                self,
                _dict=self.current_project.get_dict()
            )
            if npw.output:
                self.current_project = core.PhaserProject()
                self.current_project.fill_from_dict(npw.output)
                self.set_title()
                # if your change the bg color, or the size of project
                # all already created canvas must be updated
                self.update_canvases()

if __name__ == '__main__':
    top = PhaserEditor()
    top.focus_force()
    # windows.about.AboutWindow(top)
    top.mainloop()