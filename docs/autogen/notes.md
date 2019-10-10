
Processed 23303 files
# Clang/LLVM Notes
These are automatically generated notes from the source code of Clang/LLVM 8.0.1.

**FIXME** and **TODO** signify some remaining work

# Index

1. [How to add your own optimization level in `opt` tool?](#ADDOPT_O4)
1. [How is pass dependence specified? (Legacy PM)](#HOW_PASS_DEPENDENCE_IS_SPECIFIED_LEGACY)
1. [How is pass dependence specified? (New PM)](#HOW_PASS_DEPENDENCE_IS_SPECIFIED_NEW_PM)
1. [How is a pass registered? (Legacy PM)](#HOW_TO_REGISTER_PASS_LEGACY)
1. [How is a pass registered? (New PM)](#HOW_TO_REGISTER_PASS_NewPM)

<a name='ADDOPT_O4'></a>
## How to add your own optimization level in `opt` tool?
Lets add optimization level O4 next to the predefined O3 level.
Here we are adding a command line option `-O4` exactly the
way `-O3` has been already defined.


[opt.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/tools/opt/opt.cpp)

    static cl::opt<bool>
    OptLevelO3("O3",
               cl::desc("Optimization level 3. Similar to clang -O3"));
    
    static cl::opt<bool>
    OptLevelO4("O4",
               cl::desc("Optimization level 4. (LEG - experiment)"));
### 
Check if `-O4` is given as argument (via command line),
and then add custom passes to the `Passes` object.


[opt.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/tools/opt/opt.cpp)

      // Create a PassManager to hold and optimize the collection of passes we are
      // about to build.
      OptCustomPassManager Passes;
      if (OptLevelO4.getValue()) {
        StringRef str = "domtree-ad";
        llvm::errs() << "AD: tools/opt/opt.cpp main() gvn PassInfo: ";
        llvm::errs() << Registry.getPassInfo(str) << "\n";
        addPass(Passes, Registry.getPassInfo(str)->getNormalCtor()());
        // Check that the module is well formed on completion of optimization //AD:delit
        // if (!NoVerify && !VerifyEach)
        //   Passes.add(createVerifierPass());
    
        // raw_ostream *OS = nullptr;
        // OS = &Out->os();
        // Passes.add(createBitcodeWriterPass(*OS, PreserveBitcodeUseListOrder,
        //                                    EmitSummaryIndex, EmitModuleHash));
        Passes.run(*M); //>> run the pass manager
        return 22; //>> return a unique number to confirm
      }


<a name='HOW_PASS_DEPENDENCE_IS_SPECIFIED_LEGACY'></a>
## How is pass dependence specified? (Legacy PM)
To specify dependence, the function `getAnalysisUsage()` is overridden.
For example, `gvn` (`llvm::gvn::GVNLegacyPass`) analysis
specifies dependence on nine other passes as follows,


[GVN.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Transforms/Scalar/GVN.cpp)

      void getAnalysisUsage(AnalysisUsage &AU) const override {
        AU.addRequired<AssumptionCacheTracker>();
        AU.addRequired<DominatorTreeWrapperPass>();
        AU.addRequired<TargetLibraryInfoWrapperPass>();
        if (!NoMemDepAnalysis)
          AU.addRequired<MemoryDependenceWrapperPass>();
        AU.addRequired<AAResultsWrapperPass>();
    
        AU.addPreserved<DominatorTreeWrapperPass>();
        AU.addPreserved<GlobalsAAWrapperPass>();
        AU.addPreserved<TargetLibraryInfoWrapperPass>();
        AU.addRequired<OptimizationRemarkEmitterWrapperPass>();
      }
### 
The snippet below initializes the `gvn` pass along
with its dependencies.


* **FIXME:** Why initialize this way?
* **FIXME:** Why initialize only seven out of nine dependencies.


[GVN.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Transforms/Scalar/GVN.cpp)

    INITIALIZE_PASS_BEGIN(GVNLegacyPass, "gvn", "Global Value Numbering", false, false)
    INITIALIZE_PASS_DEPENDENCY(AssumptionCacheTracker)
    INITIALIZE_PASS_DEPENDENCY(MemoryDependenceWrapperPass)
    INITIALIZE_PASS_DEPENDENCY(DominatorTreeWrapperPass)
    INITIALIZE_PASS_DEPENDENCY(TargetLibraryInfoWrapperPass)
    INITIALIZE_PASS_DEPENDENCY(AAResultsWrapperPass)
    INITIALIZE_PASS_DEPENDENCY(GlobalsAAWrapperPass)
    INITIALIZE_PASS_DEPENDENCY(OptimizationRemarkEmitterWrapperPass)
    INITIALIZE_PASS_END(GVNLegacyPass, "gvn", "Global Value Numbering", false, false)


<a name='HOW_PASS_DEPENDENCE_IS_SPECIFIED_NEW_PM'></a>
## How is pass dependence specified? (New PM)
The new pass manager directly specifies the dependence
in the `run()` method. The call `AM.getResult<>()` is a blocking call,
that starts the given analysis if its results are not cached, and returns
the results.


[GVN.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Transforms/Scalar/GVN.cpp)

    PreservedAnalyses GVN::run(Function &F, FunctionAnalysisManager &AM) {
      // FIXME: The order of evaluation of these 'getResult' calls is very
      // significant! Re-ordering these variables will cause GVN when run alone to
      // be less effective! We should fix memdep and basic-aa to not exhibit this
      // behavior, but until then don't change the order here.
      auto &AC = AM.getResult<AssumptionAnalysis>(F);
      auto &DT = AM.getResult<DominatorTreeAnalysis>(F);
      auto &TLI = AM.getResult<TargetLibraryAnalysis>(F);
      auto &AA = AM.getResult<AAManager>(F);
      auto &MemDep = AM.getResult<MemoryDependenceAnalysis>(F);
      auto *LI = AM.getCachedResult<LoopAnalysis>(F);
      auto &ORE = AM.getResult<OptimizationRemarkEmitterAnalysis>(F);
      bool Changed = runImpl(F, AC, DT, TLI, AA, &MemDep, LI, &ORE);
      if (!Changed)
        return PreservedAnalyses::all();
      PreservedAnalyses PA;
      PA.preserve<DominatorTreeAnalysis>();
      PA.preserve<GlobalsAA>();
      PA.preserve<TargetLibraryAnalysis>();
      return PA;
    }
### 
The snippet below shows the definition of the `getResult<>()` function.
It expects that the given pass is already registered and
runs it if its results are not cached.


**TODO:** Explore how the results are actually fetched/managed?


[PassManager.h](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/include/llvm/IR/PassManager.h)

      /// Get the result of an analysis pass for a given IR unit.
      ///
      /// Runs the analysis if a cached result is not available.
      template <typename PassT>
      typename PassT::Result &getResult(IRUnitT &IR, ExtraArgTs... ExtraArgs) {
        assert(AnalysisPasses.count(PassT::ID()) &&
               "This analysis pass was not registered prior to being queried");
        ResultConceptT &ResultConcept =
            getResultImpl(PassT::ID(), IR, ExtraArgs...);
    
        using ResultModelT =
            detail::AnalysisResultModel<IRUnitT, PassT, typename PassT::Result,
                                        PreservedAnalyses, Invalidator>;
    
        return static_cast<ResultModelT &>(ResultConcept).Result;
      }


<a name='HOW_TO_REGISTER_PASS_LEGACY'></a>
## How is a pass registered? (Legacy PM)
We create an object of the `RegisterPass` class template,
from the file defining our pass.
The template is instantiated to the `Hello` pass we want
registered here. The two arguments to the constructer
are the:
1. First: A command line argument needed to invoke the pass (`-hello` in this case)
2. Second: A short meaningful description for the users of the pass.


The name `X` is itself not used anywhere (although the object created is).


[Hello.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Transforms/Hello/Hello.cpp)

    static RegisterPass<Hello> X("hello", "Hello World Pass");
### 
The constructor of `RegisterPass` calls the `PassRegistry::getPassRegistry()->registerPass()`
method to register the pass with the `PassRegistry`.


Note that `RegisterPass` is a subclass of `PassInfo` class.


The `RegisterPass` constructor takes four arguments:
1. `StringRef PassArg`: the command line name of the argument (like `-hello`)
2. `StringRef Name`: a short meaningful description of the pass
3. `bool CFGOnly`: ??
4. `bool is_analysis`: Is this pass just an analysis pass?


[PassSupport.h](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/include/llvm/PassSupport.h)

    //===---------------------------------------------------------------------------
    /// RegisterPass<t> template - This template class is used to notify the system
    /// that a Pass is available for use, and registers it into the internal
    /// database maintained by the PassManager.  Unless this template is used, opt,
    /// for example will not be able to see the pass and attempts to create the pass
    /// will fail. This template is used in the follow manner (at global scope, in
    /// your .cpp file):
    ///
    /// static RegisterPass<YourPassClassName> tmp("passopt", "My Pass Name");
    ///
    /// This statement will cause your pass to be created by calling the default
    /// constructor exposed by the pass.
    template <typename passName> struct RegisterPass : public PassInfo {
      // Register Pass using default constructor...
      RegisterPass(StringRef PassArg, StringRef Name, bool CFGOnly = false,
                   bool is_analysis = false)
          : PassInfo(Name, PassArg, &passName::ID,
                     PassInfo::NormalCtor_t(callDefaultCtor<passName>), CFGOnly,
                     is_analysis) {
        PassRegistry::getPassRegistry()->registerPass(*this);
      }
    };
### 
Looking at the constructor definition closely,
notice how `&passName::ID` is used to steal the address
of the `ID` variable defined in the pass class.
This address is used as an identifier of the analysis
at various places in LLVM.


In order for LLVM to create instances of the pass,
`PassInfo::NormalCtor_t(callDefaultCtor<passName>)` is used,
which effectively stores a pointer to a function that can
return new object of the pass. `callDefaultCtor<passName>`
is actually that function's name.


[PassSupport.h](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/include/llvm/PassSupport.h)

          : PassInfo(Name, PassArg, &passName::ID,
                     PassInfo::NormalCtor_t(callDefaultCtor<passName>), CFGOnly,
                     is_analysis) {
        PassRegistry::getPassRegistry()->registerPass(*this);
      }
### 
Below is the definition of the `callDefaultCtor()` function.


[PassSupport.h](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/include/llvm/PassSupport.h)

    template <typename PassName> Pass *callDefaultCtor() { return new PassName(); }


<a name='HOW_TO_REGISTER_PASS_NewPM'></a>
## How is a pass registered? (New PM)
All passes are manually registerd in the file `PassRegistry.def`.
Lets take an example of the `domtree` pass.
Its a function analysis pass which has to be registered using the macro
`FUNCTION_ANALYSIS` in the file `PassRegistry.def`.


[PassRegistry.def](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Passes/PassRegistry.def)

    FUNCTION_ANALYSIS("domtree", DominatorTreeAnalysis())
### 
The `PassRegistry.def` is included at various places
in `PassBuilder.cpp` with appropriate macro definitions.
The line `FAM.registerPass(...` registers the passes given in the macro.


**FIXME:** It is not clear how the `NAME` in the macro is used.
Here it can be seen that its completely thrown away.


[PassBuilder.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Passes/PassBuilder.cpp)

    void PassBuilder::registerFunctionAnalyses(FunctionAnalysisManager &FAM) {
    #define FUNCTION_ANALYSIS(NAME, CREATE_PASS)                                   \
      FAM.registerPass([&] { return CREATE_PASS; });
    #include "PassRegistry.def"
    
      for (auto &C : FunctionAnalysisRegistrationCallbacks)
        C(FAM);
    }
### 
Note that appropriate declarations have to be included
in `PassBuilder.cpp` for this to work.
In our case, for `DominatorTreeAnalysis`
we need to include `Dominators.h`.


[PassBuilder.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/llvm-clang8.0.1-git/llvm/lib/Passes/PassBuilder.cpp)

    #include "llvm/IR/Dominators.h"
<br><br><br>
<div class='footer'> <br/> &copy; LEG Team <br/> </div>
