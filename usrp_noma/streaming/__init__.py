"""
ZMQ veri akisi modulu: USRP E310 ile host bilgisayar arasi IQ veri aktarimi.
"""


def __getattr__(name):
    if name == "ZMQStreamer":
        from usrp_noma.streaming.zmq_streamer import ZMQStreamer
        return ZMQStreamer
    raise AttributeError(f"module 'usrp_noma.streaming' has no attribute {name!r}")


__all__ = ["ZMQStreamer"]
