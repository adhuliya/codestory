

# Index

1. [How is a pass registered? (Legacy PM)](#HOW_TO_REGISTER_PASS_LEGACY)

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


[Hello.cpp](file:///home/codeman/.itsoflife/mydata/git/ws/codestory-git/sample/Hello.cpp)

<pre class='language-cpp line-numbers' data-start='52'><code>
    static RegisterPass<Hello> X("hello", "Hello World Pass");
</code></pre>
### 
The constructor of `RegisterPass` calls the `PassRegistry::getPassRegistry()->registerPass()`
method to register the pass with the `PassRegistry`.


Note that `RegisterPass` is a subclass of `PassInfo` class.


The `RegisterPass` constructor takes four arguments:
1. `StringRef PassArg`: the command line name of the argument (like `-hello`)
2. `StringRef Name`: a short meaningful description of the pass
3. `bool CFGOnly`: ??
4. `bool is_analysis`: Is this pass just an analysis pass?


[PassSupport.h](file:///home/codeman/.itsoflife/mydata/git/ws/codestory-git/sample/PassSupport.h)

<pre class='language-cpp line-numbers' data-start='95'><code>
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
</code></pre>
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


[PassSupport.h](file:///home/codeman/.itsoflife/mydata/git/ws/codestory-git/sample/PassSupport.h)

<pre class='language-cpp line-numbers' data-start='124'><code>
          : PassInfo(Name, PassArg, &passName::ID,
                     PassInfo::NormalCtor_t(callDefaultCtor<passName>), CFGOnly,
                     is_analysis) {
        PassRegistry::getPassRegistry()->registerPass(*this);
      }
</code></pre>
### 
Below is the definition of the `callDefaultCtor()` function.


[PassSupport.h](file:///home/codeman/.itsoflife/mydata/git/ws/codestory-git/sample/PassSupport.h)

<pre class='language-cpp line-numbers' data-start='80'><code>
    template <typename PassName> Pass *callDefaultCtor() { return new PassName(); }
</code></pre>
