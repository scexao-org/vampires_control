from swmain.infra.tmux import find_or_create, kill_running, send_keys


def main():
    # Device control daemon
    print("Initializing the device control daemon")
    devctrl_name = "vampires_control"
    devctrl_pane = find_or_create(devctrl_name)
    kill_running(devctrl_pane)
    send_keys(devctrl_pane, "ipython -i -m device_control.daemons.vampires_daemon")
    print("Device control daemon launching.")
    print(f"Access device interfaces directly from tmux session `{devctrl_name}`")

    # temperature poller
    print("Initializing the temperature polling daemon")
    tc_status_name = "vampires_temp_daemon"
    tc_status_pane = find_or_create(tc_status_name)
    kill_running(tc_status_pane)
    send_keys(tc_status_pane, "python -m vampires_control.daemons.temp_poll_daemon")
    print(f"Temperature polling daemon launching in pane `{tc_status_name}`.")

    # QWP daemon
    print("Initializing the QWP tracking daemon in FILTER mode")
    qwp_name = "vampires_qwp_daemon"
    qwp_pane = find_or_create(qwp_name)
    kill_running(qwp_pane)
    send_keys(qwp_pane, "python -m vampires_control.daemons.qwp_daemon")
    print(f"QWP tracking daemon launching in pane `{qwp_name}`.")

    # Gen2 daemon
    print("Initializing the Gen2 daemon")
    gen2_name = "vampires_gen2_daemon"
    gen2_pane = find_or_create(gen2_name)
    kill_running(gen2_pane)
    send_keys(gen2_pane, "python -m vampires_control.gen2.main")
    print(f"Gen2 daemon launching in pane `{gen2_name}`.")


if __name__ == "__main__":
    main()
