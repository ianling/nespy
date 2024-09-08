ifeq ($(OS),Windows_NT)
	RM := del
endif

clean:
	@$(RM) nespy\*.pyd
	@$(RM) nespy\*.html
	@$(RM) nespy\*.c
