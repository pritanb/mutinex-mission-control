"""Request and response bodies. Requests check shape and type only; every business rule, and
every check with a domain message (blank names, levels out of range), stays in the services.
Responses are built explicitly from what the services return, computed values included."""
