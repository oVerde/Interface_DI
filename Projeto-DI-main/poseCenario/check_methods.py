from colega import PoseTracker
import inspect

print("Métodos do PoseTracker:")
for name, method in inspect.getmembers(PoseTracker, predicate=inspect.ismethod):
    print(f"  - {name}")

print("\nFunções do PoseTracker:")
for name in dir(PoseTracker):
    if not name.startswith('_') or name in ['__init__']:
        print(f"  - {name}")

print("\nVerificando get_smoothed_poses:")
if hasattr(PoseTracker, 'get_smoothed_poses'):
    print("✓ get_smoothed_poses EXISTE")
else:
    print("✗ get_smoothed_poses NÃO EXISTE")
