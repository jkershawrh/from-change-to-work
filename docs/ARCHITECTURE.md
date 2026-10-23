# Architecture and execution authority

The standalone presentation combines React/Vite, Three.js, React Flow, local fonts, and the Red Hat × Intel lockup. The central API and strict capability dispatcher are included with the Rust transfer crate, controller, and simulator. The console bridge and edge HTTP adapter expose bounded simulator operations around that action contract. All required application source is included in this repository.


The request path is browser → same-origin console → central action gateway → configured TLS data relay → edge inbox → Rust verification/activation/execution → local MuJoCo adapter. The edge separately fetches signed capability bytes from the central publisher through a TLS relay. A dedicated observer path reads the edge without entering the controller loop.

The console keeps infrastructure bearer tokens in private server-side files. The browser receives an expiring HttpOnly/SameSite session cookie. State-changing requests require an exact allowed Origin and client header. Viewer sessions cannot transfer, disconnect, interrupt or recover. Network requests cannot introduce destinations, executable paths, signing trust, interpreter paths or physical authority.

The recipe bank is pre-signed and locally approved during lab preparation. Its signing private key is discarded after preparation. Publication selection can choose only an existing approved digest. Rust retains compatibility, time validity, sequence floor, idle activation, task pinning and exclusive execution ownership. The durable inbox remains a transport component, not a robot safety controller.

The disconnection control closes the registered central data-plane TCP connections and gates new ones. It does not disconnect the independent management observer. The UI labels this distinction. A real deployment must decide whether that observer path is a separate management VLAN, cellular link or site-local monitoring service; the current lab does not qualify any particular topology.

Interruption verifies the known Rust process and exact action request before signaling it. Intent is durably recorded before the side effect. An uncertain acknowledgement does not authorize repeating a signal or restarting motion. Rust recovery reconciles orphaned execution; a new deliberate action is required for another run. Service shutdown also signals an owned running simulator executor, leaving uncertain durable state for explicit recovery after restart.

The existing scalar recipe profile is not a general learned-policy installer. New use cases retain this delivery/lifecycle structure but need a reviewed compiled executor profile, business acceptance, compatibility/resource declarations and fault/trace tests. ROS 2, an OEM SDK, PLC/OPC UA and mobile-robot protocols are potential local adapter choices, not implemented drivers in this repo.

No immutable external ledger, device attestation, production fleet identity/key rotation, safety certification or hard-real-time control is claimed. SQLite snapshots and hashes make the software evidence inspectable; they do not make a trusted local host adversary-proof.
