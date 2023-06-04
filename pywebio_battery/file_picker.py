import os.path
import pathlib
import typing
from datetime import datetime

from pywebio.io_ctrl import output_register_callback
from pywebio.output import *
from pywebio.output import _put_message
from pywebio.pin import *
from pywebio.session import run_js, eval_js
from pywebio.session import set_env
from pywebio.utils import random_str


class FilePicker:
    @staticmethod
    def readable_size(byte_size: int):
        for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if byte_size < 1024.0:
                return f"{byte_size:.2f} {unit}" if unit != 'bytes' else f"{byte_size} {unit}"
            byte_size /= 1024.0
        return f"{byte_size:.2f} PB"

    def __init__(self, path: str = '/', multiple: bool = False,
                 accept: typing.Union[str, typing.List[str]] = None, show_hidden_files: bool = False):
        self.root_path = pathlib.Path(path).expanduser()
        self.multiple = multiple
        self.accept = accept if isinstance(accept, str) else tuple(accept)
        self.show_hidden_files = show_hidden_files
        self.instance_id = 'file_picker_' + random_str(10)
        self.selected_files = []

        self.init()

    def init(self):
        callback_id = output_register_callback(self.change_dir_or_add_file)
        _put_message(color='secondary', contents=[
            put_scope(f"{self.instance_id}_path")
        ]).style('font-size: 12px; padding: 8px 12px; margin-bottom: 8px;')
        self.show_path(self.root_path)

        put_datatable(
            self.path_info(self.root_path),
            id_field='id',
            multiple_select=self.multiple if self.multiple else None,
            onselect=self.on_select,
            column_args={
                "id": {"hide": True},
                "size": {"cellStyle": {"color": "grey"}},
                "date_modified": {"cellStyle": {"color": "grey"}}
            },
            grid_args={
                "onCellDoubleClicked": JSFunction("event", f"WebIO.pushData(event.node.id, {callback_id!r})")
            },
            instance_id=self.instance_id,
            cell_content_bar=False,
        )
        put_scope(f"{self.instance_id}-action_btn")
        _put_message(color='secondary', contents=[
            put_markdown("**Selected Files** (click file name to unselect):").style("margin-bottom: 4px;"),
            put_scope(f"{self.instance_id}_files").style("margin-left: 8px;")
        ]).style('font-size: 14px; padding: 8px 12px')

    def on_select(self, files: typing.Union[typing.List[str], str]):
        if not isinstance(files, list):  # single select
            files = [files]
        with use_scope(f"{self.instance_id}-action_btn", clear=True):
            if len(files) == 1:
                f = pathlib.Path(files[0])
                put_button(
                    f"Open Folder ({f.name})" if f.is_dir() else f"Select File ({f.name})",
                    onclick=lambda: self.change_dir_or_add_file(str(f)),
                    color='secondary', small=True,
                )
            elif len(files) > 1:
                files = [pathlib.Path(f) for f in files if pathlib.Path(f).is_file()]
                if files:
                    put_button(
                        f"Select {len(files)} Files",
                        onclick=lambda: self.add_files(files),
                        color='secondary', small=True,
                    )

    def show_files(self):
        with use_scope(f"{self.instance_id}_files", clear=True):
            for file in self.selected_files:
                put_text(file).onclick(lambda file=file: [
                    self.selected_files.remove(file) if file in self.selected_files else None,
                    self.show_files()
                ]).style('margin-bottom: 0px;')

    def show_path(self, path: pathlib.Path):
        parts = path.relative_to(self.root_path).parts
        with use_scope(f"{self.instance_id}_path", clear=True):
            put_text("Current Path: .", inline=True).onclick(
                lambda: self.change_dir_or_add_file(str(self.root_path)))
            for i, part in enumerate(parts):
                put_text(' / ', inline=True).style('color: #939393;')
                curr_path = str(self.root_path / pathlib.Path(*parts[:i + 1]))
                put_text(part, inline=True).onclick(lambda path=curr_path: self.change_dir_or_add_file(path))

    def path_info(self, path: pathlib.Path):
        files = []
        for f in path.iterdir():
            if not self.show_hidden_files and f.name.startswith('.'):
                continue
            if f.is_dir() or f.name.lower().endswith(self.accept):
                file = {
                    "id": str(f),
                    "name": f"{f.name}" if f.is_file() else f"📁 {f.name}/",
                }
                try:
                    file.update({
                        "size": self.readable_size(f.stat().st_size) if f.is_file() else '--',
                        "date_modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    })
                except Exception:
                    pass
                files.append(file)

        files.sort(key=lambda f: (f["name"][0] != "📁", f["name"].lower()))
        if path != self.root_path:
            files.insert(0, {"name": "📁 ../", "size": '--', "id": str(path.parent.resolve()), "date_modified": '--'})
        return files

    def change_dir_or_add_file(self, path: str):
        path = pathlib.Path(path)
        if path.is_dir():
            if not path.is_relative_to(self.root_path):
                toast("No permission to access the path", color="error")
                return
            self.show_path(path)
            datatable_update(self.instance_id, self.path_info(path))
            self.on_select([])
        else:
            self.add_files([path])

    def add_files(self, paths: typing.List[pathlib.Path]):
        for path in paths:
            file = str(path.relative_to(self.root_path))
            if file not in self.selected_files:
                if not self.multiple:
                    self.selected_files.clear()
                self.selected_files.append(file)
        self.show_files()

        # unselect the datatable row
        run_js("window[instance_id].then(grid => grid.api.deselectAll())",
               instance_id=f"ag_grid_{self.instance_id}_promise")
        clear(f"{self.instance_id}-action_btn")


def file_picker(
        path: str,
        multiple: bool = False,
        accept: typing.Union[str, typing.List[str]] = '',
        cancelable: bool = False,
        title: str = 'File Picker',
        show_hidden_files: bool = False,
) -> typing.Union[str, typing.List[str], None]:
    """
    A file picker widget that allows you to select files from the local file system where PyWebIO is running.

    :param str path: The root path of the file picker. ``~`` can be used to represent the user's home directory.
    :param bool multiple: Whether to allow multiple files to be selected.
    :param str accept: Acceptable file type, case-insensitive. Can be a string or a list of strings.
       e.g. ``accept='pdf'``, ``accept=['jpg', 'png']``.  Default is to accept any file.
    :param bool cancelable: Whether to allow the user to cancel the file picker.
       By default, the user can only close the file picker by selecting the file.
    :param str title: The title of the file picker popup.
    :param show_hidden_files: Whether to show hidden files/folders.
    :return: The selected file path or a list of file paths.
        ``None`` if the user cancels the file picker.

    .. exportable-codeblock::
        :name: battery-file_picker
        :summary: Select files from the local file system

        files = file_picker('.', multiple=True, accept='py')
        put_text(files)
    """
    no_animation = eval_js("document.body.classList.contains('no-animation')")
    if not no_animation:
        # disable animation to get better UI experience
        set_env(output_animation=False)

    with popup(title, size='large', closable=False):
        picker = FilePicker(path, multiple, accept, show_hidden_files)
        buttons = [{'label': 'CONFIRM', 'value': True}]
        if cancelable:
            buttons.append({'label': 'CANCEL', 'value': False, 'color': 'warning'})
        put_actions(f"picker-{picker.instance_id}", buttons=buttons).style('margin-top: 1rem; float: right;')

    while True:
        submit = pin_wait_change(f"picker-{picker.instance_id}")
        if not cancelable and not picker.selected_files:
            toast("Please select a file", color='warn')
        else:
            break

    close_popup()

    if not no_animation:
        set_env(output_animation=True)

    if not submit['value']:  # cancel button clicked
        return None

    selected_files = [
        os.path.join(picker.root_path, f)
        for f in picker.selected_files
    ]

    if multiple:
        return selected_files
    elif selected_files:
        return selected_files[0]
