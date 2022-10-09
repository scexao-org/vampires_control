CONF_DIR := "conf"

SERVICE_FILES = $(CONF_DIR)/services/%.service
SERVICE_DEST = /etc/systemd/user


all: python_library

python_library:
	@echo "Installing python library"
	python -m pip install .

$(SERVICE_FILES):
	@echo "Copying service files to $(SERVICE_DEST)"
	cp $@ $(SERVICE_DEST)

install: python_library $(SERVICE_FILES)

.PHONY: clean uninstall

clean:
	rm -rf vampires_control.egg-info*
	rm -rf build

uninstall: uninstall_python rm_conf_files

uninstall_python:
	python -m pip uninstall vampires_control

rm_conf_files:
	rm -rf $(SERVICE_DEST)/vampires*.service
	