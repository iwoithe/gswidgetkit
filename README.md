# gswidgetkit

Various custom widgets for wxPython, created to be used in [Gimel Studio](https://github.com/GimelStudio/GimelStudio).

Highly inspired by the look and functionality of Blender and Sketch widgets. *Currently, it uses styles specific to Gimel Studio, but they can be customized as you like in ``constants.py``.*


## Widget Contents

- [x] Buttons (with text + icon or just icon)
- [x] Number Field (similar to Blender's Number Field control)
- [x] Color Picker
- [x] Textctrl
- [x] Checkbox
- [x] Tooltip
- [x] Static Label
- [x] Dropdown (still needs work)
- [ ] Color Picker Popup
- [ ] Image Picker
- [ ] Radio Buttons
- [ ] Scrollbar


## Get Started

Simply ```pip install gswidgetkit``` and run the ```demo.py``` file from this repository for a demo of the widgets.


## Contributing

All contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details. Feel free to open a PR or ask questions.


## Releasing on PyPI

Navigate to the root directory

Run ``py -m build``

Then run ``twine upload dist/*`` and follow the prompts.


## License

Licensed under the Apache 2.0 License. Feel free to use these widgets as a starting point, etc for your own projects.
