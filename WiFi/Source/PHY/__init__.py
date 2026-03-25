def __getattr__(name: str):
    if name == 'PHY':
        from WiFi.Source.PHY.phy import PHY as _PHY
        return _PHY
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
