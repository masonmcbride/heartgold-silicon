/* Native process entry; all game initialization remains in original code. */
extern void NitroMain(void);
int main(void)
{
    NitroMain();
    return 0;
}
