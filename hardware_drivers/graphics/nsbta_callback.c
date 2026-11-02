/* Native pointer storage for lib/asm/nnsys_data.s:gAnmCalcFuncNsBta.
 * The resource format remains unchanged; this is writable runtime callback data.
 */
#include <nnsys/g3d_anm_mat_internal.h>
#include <field/map_prop_render.h>
_Static_assert(sizeof(G3dFuncAnmMat) == 8, "ARM64 callback storage");
_Static_assert(__builtin_types_compatible_p(NNSG3dFuncAnmMat, G3dFuncAnmMat),
               "public and calculator callback ABI");
NNSG3dFuncAnmMat gAnmCalcFuncNsBta = NNSi_G3dAnmCalcNsBta;
