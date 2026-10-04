from cubie import DeviceResources
from typing import Optional

class VmArena:
    def __init__(
        self,
        os: str,
        network: bool = False, # Hard-Off per default (Air-Gapped)
        resources: Optional[DeviceResources] = None,
        env_path: Optional[str] = None,
    ):
        self.os = os
        self.network = network
        self.resources = resources or DeviceResources()
        self.env_path = env_path