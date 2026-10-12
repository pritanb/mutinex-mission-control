"""One router per area. Each route validates its input, calls one service and serialises the
result; refusals are turned into responses by `api.errors`."""
