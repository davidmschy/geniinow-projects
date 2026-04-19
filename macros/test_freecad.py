import FreeCAD as App
import Part
import os

print("FreeCAD test starting...")
doc = App.newDocument('Test')
box = doc.addObject('Part::Box', 'Box')
box.Length = 10
box.Width = 10
box.Height = 10
doc.recompute()

out_dir = '/Users/davidschy/geniinow-projects/modules/detail_library'
os.makedirs(out_dir, exist_ok=True)
doc.saveAs(f'{out_dir}/Test.FCStd')
App.closeDocument('Test')
print("Test successful!")

# Force exit to avoid interactive mode
import sys
sys.exit(0)
