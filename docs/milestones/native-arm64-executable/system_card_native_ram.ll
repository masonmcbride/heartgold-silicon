; ModuleID = '/Users/mason/w/cs/fun/heartgold-silicon/upstream/pokeheartgold/src/system_card.c'
source_filename = "/Users/mason/w/cs/fun/heartgold-silicon/upstream/pokeheartgold/src/system_card.c"
target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64-apple-macosx15.0.0"

@s_HW_MAIN_MEM_SYSTEM = external global [1024 x i8]
%struct.RomHeaderFields = type { [12 x i8], i32, i16, [46 x i8], i32, i32, i32, i32 }
%struct.FSArchive = type { %union.anon, ptr, ptr, %struct._OSThreadQueue, %struct._OSThreadQueue, i32, %struct.FSFileLink, i32, i32, i32, i32, i32, i32, i32, ptr, ptr, ptr, ptr, ptr, i32 }
%union.anon = type { i32 }
%struct._OSThreadQueue = type { ptr, ptr }
%struct.FSFileLink = type { ptr, ptr }
%struct.FSFile = type { %struct.FSFileLink, ptr, i32, i32, i32, [1 x %struct._OSThreadQueue], %union.anon.0, %union.anon.2, ptr }
%union.anon.0 = type { %struct.anon.1 }
%struct.anon.1 = type { %struct.FSDirPos, i32 }
%struct.FSDirPos = type { ptr, i16, i16, i32 }
%union.anon.2 = type { %struct.FSFindPathInfo }
%struct.FSFindPathInfo = type { %struct.FSDirPos, ptr, i32, %union.anon.3 }
%union.anon.3 = type { ptr }
%struct.anon = type { i32, i32, i32, i32 }

@s_HW_MAIN_MEM = external global [8388608 x i8], align 1
@sRomArchiveName = internal constant [4 x i8] c"rom\00", align 1

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define void @SystemCard_InitRomArchive() #0 {
  %1 = alloca ptr, align 8
  %2 = alloca ptr, align 8
  store ptr getelementptr (i8, ptr @s_HW_MAIN_MEM, i64 8384512), ptr %2, align 8
  %3 = call i32 @FS_IsAvailable()
  %4 = icmp ne i32 %3, 0
  br i1 %4, label %6, label %5

5:                                                ; preds = %0
  call void @OS_Terminate()
  br label %43

6:                                                ; preds = %0
  %7 = load i32, ptr getelementptr (i8, ptr @s_HW_MAIN_MEM, i64 8384524), align 4
  %8 = icmp eq i32 %7, 0
  br i1 %8, label %9, label %10

9:                                                ; preds = %6
  call void @CARD_Init()
  call void @MI_CpuCopy8(ptr noundef inttoptr (i64 add (i64 ptrtoint (ptr @s_HW_MAIN_MEM to i64), i64 8388096) to ptr), ptr noundef getelementptr (i8, ptr @s_HW_MAIN_MEM, i64 8384512), i32 noundef 352)
  call void @MI_CpuCopy8(ptr noundef inttoptr (i64 add (i64 ptrtoint (ptr @s_HW_MAIN_MEM to i64), i64 8388096) to ptr), ptr noundef getelementptr (i8, ptr @s_HW_MAIN_MEM, i64 8387200), i32 noundef 352)
  store i32 1245791297, ptr getelementptr (i8, ptr @s_HW_MAIN_MEM, i64 8384524), align 4
  br label %10

10:                                               ; preds = %9, %6
  %11 = call ptr @FS_FindArchive(ptr noundef @sRomArchiveName, i32 noundef 3)
  store ptr %11, ptr %1, align 8
  %12 = load ptr, ptr %2, align 8
  %13 = getelementptr inbounds %struct.RomHeaderFields, ptr %12, i32 0, i32 6
  %14 = load i32, ptr %13, align 4
  %15 = load ptr, ptr %1, align 8
  %16 = getelementptr inbounds %struct.FSArchive, ptr %15, i32 0, i32 8
  store i32 %14, ptr %16, align 4
  %17 = load ptr, ptr %2, align 8
  %18 = getelementptr inbounds %struct.RomHeaderFields, ptr %17, i32 0, i32 7
  %19 = load i32, ptr %18, align 4
  %20 = load ptr, ptr %1, align 8
  %21 = getelementptr inbounds %struct.FSArchive, ptr %20, i32 0, i32 9
  store i32 %19, ptr %21, align 8
  %22 = load ptr, ptr %2, align 8
  %23 = getelementptr inbounds %struct.RomHeaderFields, ptr %22, i32 0, i32 4
  %24 = load i32, ptr %23, align 4
  %25 = load ptr, ptr %1, align 8
  %26 = getelementptr inbounds %struct.FSArchive, ptr %25, i32 0, i32 10
  store i32 %24, ptr %26, align 4
  %27 = load ptr, ptr %2, align 8
  %28 = getelementptr inbounds %struct.RomHeaderFields, ptr %27, i32 0, i32 5
  %29 = load i32, ptr %28, align 4
  %30 = load ptr, ptr %1, align 8
  %31 = getelementptr inbounds %struct.FSArchive, ptr %30, i32 0, i32 11
  store i32 %29, ptr %31, align 8
  %32 = load ptr, ptr %2, align 8
  %33 = getelementptr inbounds %struct.RomHeaderFields, ptr %32, i32 0, i32 1
  %34 = load i32, ptr %33, align 4
  %35 = icmp ne i32 %34, 1245791297
  br i1 %35, label %42, label %36

36:                                               ; preds = %10
  %37 = load ptr, ptr %2, align 8
  %38 = getelementptr inbounds %struct.RomHeaderFields, ptr %37, i32 0, i32 2
  %39 = load i16, ptr %38, align 4
  %40 = zext i16 %39 to i32
  %41 = icmp ne i32 %40, 12592
  br i1 %41, label %42, label %43

42:                                               ; preds = %36, %10
  call void @OS_Terminate()
  br label %43

43:                                               ; preds = %5, %42, %36
  ret void
}

declare i32 @FS_IsAvailable() #1

declare void @OS_Terminate() #1

declare void @CARD_Init() #1

declare void @MI_CpuCopy8(ptr noundef, ptr noundef, i32 noundef) #1

declare ptr @FS_FindArchive(ptr noundef, i32 noundef) #1

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define void @SystemCard_RebootIntoFile(ptr noundef %0) #0 {
  %2 = alloca ptr, align 8
  %3 = alloca %struct.FSFile, align 8
  store ptr %0, ptr %2, align 8
  call void @FS_InitFile(ptr noundef %3)
  %4 = load ptr, ptr %2, align 8
  %5 = call i32 @FS_OpenFile(ptr noundef %3, ptr noundef %4)
  %6 = icmp ne i32 %5, 0
  br i1 %6, label %7, label %11

7:                                                ; preds = %1
  %8 = getelementptr inbounds %struct.FSFile, ptr %3, i32 0, i32 6
  %9 = getelementptr inbounds %struct.anon, ptr %8, i32 0, i32 1
  %10 = load i32, ptr %9, align 4
  store i32 %10, ptr getelementptr (i8, ptr @s_HW_MAIN_MEM_SYSTEM, i64 44), align 4
  call void @OS_ResetSystem(i32 noundef 0)
  br label %11

11:                                               ; preds = %7, %1
  ret void
}

declare void @FS_InitFile(ptr noundef) #1

declare i32 @FS_OpenFile(ptr noundef, ptr noundef) #1

declare void @OS_ResetSystem(i32 noundef) #1

attributes #0 = { noinline nounwind optnone ssp uwtable(sync) "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #1 = { "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 2, !"SDK Version", [2 x i32] [i32 15, i32 5]}
!1 = !{i32 1, !"wchar_size", i32 4}
!2 = !{i32 8, !"PIC Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 1}
!4 = !{i32 7, !"frame-pointer", i32 1}
!5 = !{!"Apple clang version 17.0.0 (clang-1700.0.13.5)"}
